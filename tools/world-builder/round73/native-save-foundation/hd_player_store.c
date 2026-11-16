/* Round 73G: private-only native player save bridge.
 * Preserves legacy serialized creature inventory ABI. Every player-file save
 * must preserve existing claim receipts from the SAME compressed record.
 * A staged grant is committed with its receipt in one atomic replacement.
 * NO TREASURE COMMAND calls this file until guardian/ownership/persistence
 * and native verification gates are passed.
 */
#define _GNU_SOURCE
#include "hd_player_store.h"
#include "atomic_player_snapshot.h"
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <sys/types.h>
#include <unistd.h>

#define HD_RAW_CAPACITY 100000U
#define HD_TREE_LIMIT 256U
#define HD_DEPTH_LIMIT 32U

extern int hd_compress_bounded(char *,char *,int,int);
extern int hd_uncompress_bounded(char *,char *,int,int);
extern int write_crt_to_mem(char *, creature *, int);
extern int read_crt_from_mem(char *, creature *);

static int valid_name(const char *s) {
    size_t i;
    if (!s || s[0] < 'A' || s[0] > 'Z') return 0;
    for (i=1; i<15U; ++i) {
        if (!s[i]) return i >= 2U;
        if (!((s[i] >= 'A' && s[i] <= 'Z') ||
              (s[i] >= 'a' && s[i] <= 'z'))) return 0;
    }
    return 0;
}
static int native_name(const char *s, const char *name) {
    size_t n;
    if (!s || !name) return 0;
    n = strlen(name);
    return n < 80U && !memcmp(s, name, n) && s[n] == '\0';
}

/* Total-size preflight prevents the old recursive writer from crossing a
 * 100,000-byte allocation, including repeated/cyclic object pointers. */
struct size_walk {
    const object *objects[HD_TREE_LIMIT];
    size_t count, required;
};
static int walk_items(const otag *tag, unsigned depth, struct size_walk *w) {
    const otag *entry;
    size_t here = 0, i;
    if (depth > HD_DEPTH_LIMIT) return -1;
    for (entry=tag; entry; entry=entry->next_tag) {
        const object *obj = entry->obj;
        if (!obj || ++here > HD_TREE_LIMIT || w->count >= HD_TREE_LIMIT)
            return -1;
        for (i=0; i<w->count; ++i)
            if (w->objects[i] == obj) return -1;
        w->objects[w->count++] = obj;
        if (w->required > HD_RAW_CAPACITY - sizeof(object) - sizeof(int))
            return -1;
        w->required += sizeof(object) + sizeof(int);
        if (walk_items(obj->first_obj, depth+1U, w)) return -1;
    }
    return 0;
}
static int native_size(creature *crt, size_t *total) {
    struct size_walk w;
    if (!crt || !total) return -1;
    memset(&w, 0, sizeof w);
    w.required = sizeof(creature) + sizeof(int);
    if (w.required > HD_RAW_CAPACITY ||
        walk_items(crt->first_obj, 1U, &w)) return -1;
    *total = w.required;
    return 0;
}

/* Validate a flattened legacy inventory before running the original native
 * allocator-based reader. Never trust child counts in untrusted bytes. */
struct read_walk { size_t nodes; };
static int scan_children(const unsigned char *b, size_t bytes, size_t *pos,
                         unsigned depth, int count, struct read_walk *w) {
    int children;
    size_t i;
    if (depth > HD_DEPTH_LIMIT || count < 0 || (unsigned)count > HD_TREE_LIMIT ||
        w->nodes + (size_t)count > HD_TREE_LIMIT) return -1;
    for (i=0; i<(size_t)count; ++i) {
        if (*pos > bytes || bytes - *pos < sizeof(object) + sizeof(int)) return -1;
        *pos += sizeof(object);
        memcpy(&children, b+*pos, sizeof children);
        *pos += sizeof children;
        ++w->nodes;
        if (scan_children(b, bytes, pos, depth+1U, children, w)) return -1;
    }
    return 0;
}
static int scan_payload(const unsigned char *b, size_t bytes, size_t *used) {
    struct read_walk w;
    size_t pos = sizeof(creature);
    int count;
    if (!b || !used || bytes < sizeof(creature) + sizeof(int)) return -1;
    memcpy(&count, b+pos, sizeof count);
    pos += sizeof count;
    memset(&w, 0, sizeof w);
    if (scan_children(b, bytes, &pos, 1U, count, &w)) return -1;
    *used = pos;
    return 0;
}

/* Read an existing file without following symlinks. Absent save is distinct
 * from corrupt/truncated save, and never silently resets claim history. */
static int read_record(const char *name, unsigned char *raw, size_t *raw_len,
                       size_t *native_len, hd_receipt_set *receipts) {
    unsigned char packed[HD_PLAYER_COMPRESSED_LIMIT+1U];
    int dirfd=-1, fd=-1, result=-1, n;
    ssize_t got;
    size_t pos=0;
    struct stat st;
    if (!valid_name(name) || !raw || !raw_len || !native_len || !receipts)
        return -1;
    dirfd=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (dirfd < 0) goto done;
    fd=openat(dirfd,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd < 0) { if (errno==ENOENT) result=1; goto done; }
    if (fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_nlink!=1 ||
        st.st_uid!=geteuid() || st.st_size < 1 ||
        st.st_size > (off_t)HD_PLAYER_COMPRESSED_LIMIT) goto done;
    while (pos < sizeof packed) {
        got=read(fd,packed+pos,sizeof packed-pos);
        if (got < 0 && errno==EINTR) continue;
        if (got < 0) goto done;
        if (got==0) break;
        pos+=(size_t)got;
    }
    if (!pos || pos>HD_PLAYER_COMPRESSED_LIMIT) goto done;
    n=hd_uncompress_bounded((char *)packed,(char *)raw,(int)pos,HD_RAW_CAPACITY);
    if (n<0 || (size_t)n>HD_RAW_CAPACITY) goto done;
    if (scan_payload(raw,(size_t)n,native_len) ||
        !native_name((const char *)raw, name)) goto done;
    if (hd_receipt_decode(raw,(size_t)n,*native_len,receipts)) goto done;
    *raw_len=(size_t)n;
    result=0;
done:
    if (fd>=0) close(fd);
    if (dirfd>=0) close(dirfd);
    return result;
}

int hd_store_read_claim(const char *name,const char *claim_id,const char *digest) {
    unsigned char *raw;
    hd_receipt_set receipts;
    size_t size=0, used=0;
    int rc, result=-1;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if (!raw) return -1;
    rc=read_record(name,raw,&size,&used,&receipts);
    if (rc==0) result=hd_receipt_lookup(&receipts,claim_id,digest);
    free(raw);
    return result;
}

int hd_store_load_player(const char *name,creature **out) {
    unsigned char *raw;
    hd_receipt_set receipts;
    size_t size=0, used=0;
    int rc, n;
    creature *crt;
    if (!out) return -1;
    *out=NULL;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if (!raw) return -1;
    rc=read_record(name,raw,&size,&used,&receipts);
    if (rc) { free(raw); return -1; }
    crt=(creature *)malloc(sizeof *crt);
    if (!crt) { free(raw); return -1; }
    n=read_crt_from_mem((char *)raw,crt);
    free(raw);
    if (n < 0 || (size_t)n!=used) {
        /* This mismatch cannot occur for valid serialized data, but fail
         * closed instead of returning an inconsistent loaded character. */
        free(crt);
        return -1;
    }
    *out=crt;
    return 0;
}
static int store_internal(const char *name, creature *crt,
                          const char *claim, const char *digest) {
    unsigned char *raw=NULL, *packed=NULL;
    hd_receipt_set receipts;
    size_t old_len=0, old_native=0, expected=0, raw_total=0;
    int old, serialized, packed_len, lock_fd=-1, result=HD_STORE_FAILURE;
    if (!valid_name(name) || !crt || !native_name(crt->name,name) ||
        native_size(crt,&expected)) return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;
    /* Serialize writers across game processes. The receipt is still part of
     * the character save; this lock is never a claim-authority sidecar. */
    lock_fd=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (lock_fd<0 || flock(lock_fd,LOCK_EX)<0) goto done;
    old=read_record(name,raw,&old_len,&old_native,&receipts);
    if (old<0) goto done;
    if (old==1) memset(&receipts,0,sizeof receipts);
    if (claim || digest) {
        int seen;
        if (!claim || !digest) goto done;
        seen=hd_receipt_lookup(&receipts,claim,digest);
        if (seen<0) goto done;
        if (seen==1) { result=HD_STORE_ALREADY_CLAIMED; goto done; }
        if (hd_receipt_add(&receipts,claim,digest)) goto done;
    }
    serialized=write_crt_to_mem((char*)raw,crt,0);
    if (serialized<0 || (size_t)serialized!=expected) goto done;
    if (hd_receipt_encode(raw,HD_RAW_CAPACITY,expected,&receipts,&raw_total))
        goto done;
    packed_len=hd_compress_bounded((char*)raw,(char*)packed,(int)raw_total,
                                   HD_PLAYER_COMPRESSED_LIMIT);
    if (packed_len<1 || packed_len>(int)HD_PLAYER_COMPRESSED_LIMIT) goto done;
    result=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)packed_len);
    if (result==HD_SNAPSHOT_UNCERTAIN) result=HD_STORE_UNCERTAIN;
    else if (result!=HD_SNAPSHOT_OK) result=HD_STORE_FAILURE;
done:
    if (lock_fd>=0) { flock(lock_fd,LOCK_UN); close(lock_fd); }
    free(packed);
    free(raw);
    return result;
}
int hd_store_save_player(const char *name,creature *player) {
    return store_internal(name,player,NULL,NULL);
}
int hd_store_save_claim(const char *name,creature *staged,
                        const char *claim_id,const char *digest) {
    return store_internal(name,staged,claim_id,digest);
}
