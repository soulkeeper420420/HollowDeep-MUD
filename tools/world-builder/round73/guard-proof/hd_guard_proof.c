#define _GNU_SOURCE
#include "hd_guard_proof.h"
#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define HD_GPROOF_MAGIC "HD-GUARD-PROOF1"
#define HD_GPROOF_VERSION 1U
static int token(const char *s, size_t max) {
    size_t i;
    if (!s) return 0;
    for (i=0; i<max && s[i]; ++i) {
        unsigned char c=(unsigned char)s[i];
        if (!((c>='a' && c<='z') || (c>='A' && c<='Z') ||
              (c>='0' && c<='9') || c=='.' || c==':' || c=='_' || c=='-'))
            return 0;
    }
    return i>=3 && i<max;
}
static int name_ok(const char *s, size_t max) {
    size_t i;
    if (!s) return 0;
    for(i=0; i<max && s[i]; ++i) {
        unsigned char c=(unsigned char)s[i];
        if(c<32 || c>126 || c=='\t') return 0;
    }
    return i>0 && i<max && s[0]!=' ' && s[i-1]!=' ';
}
static uint32_t crc32_bytes(const void *data, size_t n) {
    const unsigned char *p=(const unsigned char *)data;
    uint32_t crc=0xffffffffU;
    size_t i;
    unsigned j;
    for(i=0; i<n; ++i) {
        crc ^= (uint32_t)p[i];
        for(j=0; j<8; ++j)
            crc=(crc >> 1) ^ (0xedb88320U & (uint32_t)(-(int)(crc & 1U)));
    }
    return ~crc;
}
static void seal(hd_guard_proof *p) {
    p->crc=crc32_bytes(p, offsetof(hd_guard_proof, crc));
}
static int hex_id(const char *s) {
    unsigned i;
    if (s[32]!='\0') return 0;
    for (i=0; i<32; ++i) if (!((s[i]>='0' && s[i]<='9') ||
                               (s[i]>='a' && s[i]<='f'))) return 0;
    return 1;
}
static int valid(const hd_guard_proof *p) {
    unsigned i, j;
    if (memcmp(p->magic, HD_GPROOF_MAGIC, sizeof(p->magic)) ||
        p->version!=HD_GPROOF_VERSION || p->room<10000U ||
        p->room>=16000U || p->count<1U || p->count>HD_GPROOF_MAX ||
        !token(p->map,sizeof p->map) || !token(p->owner,sizeof p->owner) ||
        !hex_id(p->encounter_id) ||
        p->crc!=crc32_bytes(p,offsetof(hd_guard_proof,crc))) return 0;
    for(i=0; i<HD_GPROOF_MAX; ++i) {
        if(i<p->count) {
            if(!name_ok(p->names[i],sizeof p->names[i]) ||
               !hex_id(p->guardian_ids[i]) || p->dead[i]>1) return 0;
            if(p->dead[i]) {
                if(!hex_id(p->event_ids[i])) return 0;
            } else if(p->event_ids[i][0]) return 0;
            for(j=0; j<i; ++j) {
                if(!strcmp(p->names[i],p->names[j]) ||
                   !strcmp(p->guardian_ids[i],p->guardian_ids[j])) return 0;
            }
        } else if(p->names[i][0] || p->guardian_ids[i][0] ||
                  p->event_ids[i][0] || p->dead[i]) return 0;
    }
    return 1;
}
static int new_id(char out[33]) {
    static const char hex[]="0123456789abcdef";
    unsigned char b[16];
    size_t n=0, i;
    int fd=open("/dev/urandom",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    ssize_t r;
    if(fd<0) return -1;
    while(n<sizeof b) {
        r=read(fd,b+n,sizeof b-n);
        if(r<0 && errno==EINTR) continue;
        if(r<=0) {close(fd);return -1;}
        n+=(size_t)r;
    }
    if(close(fd)) return -1;
    for(i=0;i<sizeof b;++i) {out[2*i]=hex[b[i]>>4];out[2*i+1]=hex[b[i]&15];}
    out[32]='\0';
    return 0;
}
static int make_leaf(const char *map, char *leaf, size_t cap) {
    int n;
    if(!token(map,33)) return -1;
    n=snprintf(leaf,cap,"g-%s.proof",map);
    return n>0 && (size_t)n<cap ? 0:-1;
}
static int safe_target(int dirfd, const char *leaf, int *exists) {
    struct stat st;
    if(fstatat(dirfd,leaf,&st,AT_SYMLINK_NOFOLLOW)) {
        if(errno==ENOENT) {*exists=0;return 0;}
        return -1;
    }
    if(!S_ISREG(st.st_mode)||st.st_nlink!=1 || st.st_uid!=geteuid() ||
       st.st_size!=(off_t)sizeof(hd_guard_proof)) return -1;
    *exists=1;
    return 0;
}
static int open_dir_locked(const char *root) {
    int fd;
    struct stat st;
    if(!root || !*root) return -1;
    fd=open(root,O_RDONLY|O_CLOEXEC|O_DIRECTORY|O_NOFOLLOW);
    if(fd<0) return -1;
    if(fstat(fd,&st) || !S_ISDIR(st.st_mode) || st.st_uid!=geteuid() ||
       (st.st_mode & 0777)!=0700 || flock(fd,LOCK_EX)) {
        close(fd);return -1;
    }
    return fd;
}
static void close_dir(int fd) {
    if(fd>=0) {flock(fd,LOCK_UN);close(fd);}
}
static int read_existing(int dirfd, const char *leaf, hd_guard_proof *out) {
    int exists=0, fd;
    struct stat st;
    size_t n=0;
    ssize_t r;
    if(safe_target(dirfd,leaf,&exists)) return -1;
    if(!exists) return 1;
    fd=openat(dirfd,leaf,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if(fd<0) return -1;
    if(fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_nlink!=1 ||
       st.st_uid!=geteuid() || st.st_size!=(off_t)sizeof *out) {close(fd);return -1;}
    while(n<sizeof *out) {
        r=read(fd,(unsigned char *)out+n,sizeof *out-n);
        if(r<0 && errno==EINTR) continue;
        if(r<=0) {close(fd);return -1;}
        n+=(size_t)r;
    }
    if(close(fd) || !valid(out)) return -1;
    return 0;
}
static int commit_record(int dirfd, const char *leaf, hd_guard_proof *p) {
    char tmp[96], id[33];
    int fd=-1, result=HD_GPROOF_ERROR, exists, n;
    size_t written=0;
    ssize_t r;
    if(new_id(id)) return result;
    n=snprintf(tmp,sizeof tmp,".tmp-%.32s",id);
    if(n<0 || (size_t)n>=sizeof tmp) return result;
    fd=openat(dirfd,tmp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0) return result;
    seal(p);
    while(written<sizeof *p) {
        size_t left=sizeof *p-written;
#ifdef HD_GPROOF_TESTING
        if(left>9U) left=9U;
        if(getenv("HD_GPROOF_FAIL") && !strcmp(getenv("HD_GPROOF_FAIL"),"write") &&
           written>0U) goto done;
#endif
        r=write(fd,(unsigned char *)p+written,left);
        if(r<0 && errno==EINTR) continue;
        if(r<=0) goto done;
        written+=(size_t)r;
    }
    if(fsync(fd)) goto done;
    if(close(fd)) {fd=-1;goto done;}
    fd=-1;
#ifdef HD_GPROOF_TESTING
    if(getenv("HD_GPROOF_FAIL") && !strcmp(getenv("HD_GPROOF_FAIL"),"before_rename")) goto done;
#endif
    if(safe_target(dirfd,leaf,&exists)) goto done;
    if(renameat(dirfd,tmp,dirfd,leaf)) goto done;
    tmp[0]='\0';
    result=HD_GPROOF_UNCERTAIN;
#ifdef HD_GPROOF_TESTING
    if(getenv("HD_GPROOF_FAIL") && !strcmp(getenv("HD_GPROOF_FAIL"),"after_rename")) goto done;
#endif
    if(!fsync(dirfd)) result=HD_GPROOF_OK;
done:
    if(fd>=0) close(fd);
    if(tmp[0]) unlinkat(dirfd,tmp,0);
    return result;
}
int hd_guard_proof_begin(const char *root, uint32_t room, const char *map,
                         const char *owner, const char (*names)[80],
                         unsigned count, hd_guard_proof *out) {
    hd_guard_proof p;
    char leaf[64];
    int dirfd, status;
    unsigned i,j;
    if(!out || !names || !token(map,33) || !token(owner,80) ||
       room<10000U || room>=16000U || count<1U || count>HD_GPROOF_MAX ||
       make_leaf(map,leaf,sizeof leaf)) return HD_GPROOF_ERROR;
    for(i=0;i<count;++i) {
        if(!name_ok(names[i],80)) return HD_GPROOF_ERROR;
        for(j=0;j<i;++j) if(!strcmp(names[i],names[j])) return HD_GPROOF_ERROR;
    }
    dirfd=open_dir_locked(root);
    if(dirfd<0) return HD_GPROOF_ERROR;
    status=read_existing(dirfd,leaf,&p);
    if(status==1) {
        memset(&p,0,sizeof p);
        memcpy(p.magic,HD_GPROOF_MAGIC,sizeof p.magic);
        p.version=HD_GPROOF_VERSION;p.room=room;p.count=count;
        strcpy(p.map,map);strcpy(p.owner,owner);
        for(i=0;i<count;++i) {
            strcpy(p.names[i],names[i]);
            if(new_id(p.guardian_ids[i])) {status=HD_GPROOF_ERROR;goto done;}
        }
        if(new_id(p.encounter_id)) {status=HD_GPROOF_ERROR;goto done;}
        status=commit_record(dirfd,leaf,&p);
    } else if(status==0) {
        if(p.room!=room || strcmp(p.map,map) || strcmp(p.owner,owner) ||
           p.count!=count) {status=HD_GPROOF_ERROR;goto done;}
        for(i=0;i<count;++i)
            if(strcmp(p.names[i],names[i])) {status=HD_GPROOF_ERROR;goto done;}
    }
    if(status==HD_GPROOF_OK) *out=p;
done:
    close_dir(dirfd);
    return status;
}
int hd_guard_proof_mark(const char *root, hd_guard_proof *proof,
                        unsigned index) {
    hd_guard_proof now;
    char leaf[64];
    int dirfd, status;
    if(!proof || !valid(proof) || index>=proof->count ||
       make_leaf(proof->map,leaf,sizeof leaf)) return HD_GPROOF_ERROR;
    dirfd=open_dir_locked(root);
    if(dirfd<0) return HD_GPROOF_ERROR;
    status=read_existing(dirfd,leaf,&now);
    if(status!=0 || strcmp(proof->encounter_id,now.encounter_id) ||
       strcmp(proof->owner,now.owner) || proof->room!=now.room ||
       proof->count!=now.count || strcmp(proof->map,now.map)) {
        close_dir(dirfd);return HD_GPROOF_ERROR;
    }
    {
        unsigned j;
        for (j=0;j<now.count;++j)
            if (strcmp(proof->guardian_ids[j],now.guardian_ids[j]) ||
                strcmp(proof->names[j],now.names[j])) {
                close_dir(dirfd);return HD_GPROOF_ERROR;
            }
    }
    if(now.dead[index]) {
        status=HD_GPROOF_ALREADY;
    } else if(new_id(now.event_ids[index])) {
        status=HD_GPROOF_ERROR;
    } else {
        now.dead[index]=1U;
        status=commit_record(dirfd,leaf,&now);
    }
    if(status==HD_GPROOF_OK || status==HD_GPROOF_ALREADY) *proof=now;
    close_dir(dirfd);
    return status;
}
int hd_guard_proof_ready(const hd_guard_proof *p) {
    unsigned i;
    if(!p || !valid(p)) return 0;
    for(i=0;i<p->count;++i) if(!p->dead[i]) return 0;
    return 1;
}
