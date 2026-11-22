/* Round79W: feature-gated, locked native two-receipt mount save.
 * Include ONLY in hd_player_store.c AFTER hd_breath_store.inc.
 * Uses existing atomic save, HDTR1 receipt and compression functions.
 * NO player or creature binary ABI changes, commands, or movement hooks.
 */
#ifndef HD_PET_STORE_PLAYTEST
#error "Mount storage requires verified atomic player store"
#endif
#ifndef HD79_BREATH_STORE_PLAYTEST
#error "Mount storage requires verified durable Breath epoch"
#endif
#ifndef HD79_MOUNT_STORE_PLAYTEST
#error "Mount storage must be explicitly gated"
#endif
#include "hd79_mount_store.h"
#include "hd79_mount_wire.h"
#include "hd79_mount_ids.h"

static int hd79_mount_find(const hd_receipt_set *set,const char *id)
{
    size_t i;
    if (!set || !id) return -1;
    for (i=0;i<set->count;i++)
        if (!strcmp(set->entries[i].claim_id,id)) return (int)i;
    return -1;
}

/* Authoritative epoch comes from durable Breath receipt, not a caller
 * supplied epoch or a fresh random number on each mount initialization.
 */
static int hd79_mount_authoritative_epoch(const hd_receipt_set *set,
                                          char epoch[25])
{
    int idx;
    hd_breath_record breath;
    if (!set || !epoch) return -1;
    idx=hd_breath_entry(set);
    if (idx<0 || hd_breath_record_decode(
            set->entries[idx].manifest_sha256,&breath)) return -1;
    memcpy(epoch,breath.epoch,25);
    return 0;
}

/* Returns 0 = complete valid pair, 1 = completely absent, -1 = invalid.
 * Never permit a half-initialized or mixed-generation pair to be reset.
 */
static int hd79_mount_pair(const hd_receipt_set *set,
                           const char *epoch,hd79_mount_roster *out)
{
    int ia,ib;
    hd79_mount_roster restored;
    if (!set || !epoch || !out) return -1;
    ia=hd79_mount_find(set,hd79_mount_a_id);
    ib=hd79_mount_find(set,hd79_mount_b_id);
    if (ia<0 && ib<0) return 1;
    if (ia<0 || ib<0) return -1;
    if (hd79_mount_wire_decode(set->entries[ia].manifest_sha256,
                               set->entries[ib].manifest_sha256,
                               &restored)) return -1;
    if (strcmp(restored.epoch,epoch)) return -1;
    *out=restored;
    return 0;
}

int hd79_mount_store_read(const char *name,hd79_mount_roster *out)
{
    unsigned char *raw=NULL;
    hd_receipt_set receipts;
    hd79_mount_roster restored;
    char epoch[25];
    size_t used=0,native=0;
    int rc,result=HD79_MOUNT_STORE_FAILURE;
    if (!out || !valid_name(name)) return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if (!raw) return result;
    if (read_record(name,raw,&used,&native,&receipts) ||
        ((creature *)raw)->type!=PLAYER ||
        !native_name(((creature *)raw)->name,name) ||
        hd79_mount_authoritative_epoch(&receipts,epoch)) goto done;
    rc=hd79_mount_pair(&receipts,epoch,&restored);
    if (rc==1) result=HD79_MOUNT_STORE_ABSENT;
    else if (rc==0) { *out=restored; result=HD79_MOUNT_STORE_OK; }
done:
    free(raw);
    return result;
}

/* One compression and ONE native atomic rename for BOTH mount fragments. */
static int hd79_mount_transaction(const char *name,
                                  const hd79_mount_roster *expected,
                                  const hd79_mount_roster *desired,
                                  hd79_mount_roster *out)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set receipts;
    hd79_mount_roster prior,next;
    char epoch[25],old_a[65],old_b[65],new_a[65],new_b[65];
    size_t used=0,native=0,total=0;
    creature *disk;
    int lock=-1,ia,ib,rc,length,wr;
    int result=HD79_MOUNT_STORE_FAILURE;

    if (!out || !valid_name(name) || (expected==NULL)!=(desired==NULL))
        return result;
    if (expected) {
        if (!hd79_mount_roster_valid(expected) ||
            !hd79_mount_roster_valid(desired) ||
            expected->revision==UINT32_MAX ||
            desired->revision!=expected->revision+1 ||
            strcmp(expected->epoch,desired->epoch)) return result;
    }
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;

    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (lock<0 || flock(lock,LOCK_EX)<0 ||
        read_record(name,raw,&used,&native,&receipts)) goto done;
    disk=(creature *)raw;
    if (disk->type!=PLAYER || disk->level<1 || disk->level>60 ||
        !native_name(disk->name,name) ||
        hd79_mount_authoritative_epoch(&receipts,epoch)) goto done;

    rc=hd79_mount_pair(&receipts,epoch,&prior);
    if (!expected) {
        if (rc==0) { result=HD79_MOUNT_STORE_CONFLICT; goto done; }
        if (rc!=1 || hd79_mount_roster_new(&next,epoch)!=1)
            goto done;
    } else {
        if (rc==1) { result=HD79_MOUNT_STORE_CONFLICT; goto done; }
        if (rc!=0) goto done;
        if (strcmp(prior.epoch,expected->epoch) ||
            hd79_mount_wire_encode(expected,old_a,old_b)) goto done;
        ia=hd79_mount_find(&receipts,hd79_mount_a_id);
        ib=hd79_mount_find(&receipts,hd79_mount_b_id);
        if (ia<0 || ib<0) goto done;
        if (strcmp(receipts.entries[ia].manifest_sha256,old_a) ||
            strcmp(receipts.entries[ib].manifest_sha256,old_b)) {
            result=HD79_MOUNT_STORE_CONFLICT;
            goto done;
        }
        next=*desired;
    }

    if (hd79_mount_wire_encode(&next,new_a,new_b)) goto done;
    if (!expected) {
        /* Both entries are added in memory; failure of either addition
         * writes NOTHING to disk. Refuse full receipt sets. */
        if (hd_receipt_add(&receipts,hd79_mount_a_id,new_a) ||
            hd_receipt_add(&receipts,hd79_mount_b_id,new_b)) goto done;
    } else {
        ia=hd79_mount_find(&receipts,hd79_mount_a_id);
        ib=hd79_mount_find(&receipts,hd79_mount_b_id);
        if (ia<0 || ib<0) goto done;
        memcpy(receipts.entries[ia].manifest_sha256,new_a,65);
        memcpy(receipts.entries[ib].manifest_sha256,new_b,65);
    }
    if (hd_receipt_encode(raw,HD_RAW_CAPACITY,native,&receipts,&total))
        goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,
                              (int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if (length<1 || length>HD_PLAYER_COMPRESSED_LIMIT) goto done;
    wr=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)length);
    if (wr==HD_SNAPSHOT_OK || wr==HD_SNAPSHOT_UNCERTAIN) {
        *out=next;
        result=wr==HD_SNAPSHOT_OK ? HD79_MOUNT_STORE_OK :
                                     HD79_MOUNT_STORE_UNCERTAIN;
    }
done:
    if (lock>=0) { flock(lock,LOCK_UN); close(lock); }
    free(raw);
    free(packed);
    return result;
}

int hd79_mount_store_init(const char *name,hd79_mount_roster *out)
{
    return hd79_mount_transaction(name,NULL,NULL,out);
}
int hd79_mount_store_commit(const char *name,
                             const hd79_mount_roster *expected,
                             const hd79_mount_roster *next,
                             hd79_mount_roster *out)
{
    if (!expected || !next) return HD79_MOUNT_STORE_FAILURE;
    return hd79_mount_transaction(name,expected,next,out);
}
