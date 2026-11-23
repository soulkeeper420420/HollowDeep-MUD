/* Round79AB: include ONLY at end of native hd_player_store.c, following
 * hd79_mount_store.inc and hd_breath_store.inc. No player ABI changes.
 */
#if !defined(HD79_MOUNT_PRESENCE_STORE_PLAYTEST) || \
    !defined(HD79_MOUNT_STORE_PLAYTEST) || \
    !defined(HD79_BREATH_STORE_PLAYTEST)
#error "Three-receipt mount store requires mount + durable Breath store"
#endif
#include "hd79_mount_presence_store.h"
#include "hd79_mount_wire.h"
#include "hd79_mount_ids.h"

/* Read full owner snapshot. Caller verifies the real durable Breath epoch.
 * Any missing location for a populated roster is an error, not ABSENT.
 */
static int hd79_presence_snapshot(const hd_receipt_set *set,
                                  const char *epoch,
                                  hd79_mount_roster *roster,
                                  hd79_mount_presence *position)
{
    hd79_mount_roster r;
    hd79_mount_presence p;
    int base,id;
    if (!set || !epoch || !roster || !position) return -1;
    base=hd79_mount_pair(set,epoch,&r);
    id=hd79_mount_find(set,HD79_MOUNT_PRESENCE_ID);
    if (base==1 && id<0) return 1;
    if (base!=0 || id<0) return -1;
    if (hd79_presence_decode(&r,
         set->entries[id].manifest_sha256,&p)) return -1;
    *roster=r;
    *position=p;
    return 0;
}

int hd79_presence_store_read(const char *name,
                             hd79_mount_roster *roster,
                             hd79_mount_presence *position)
{
    unsigned char *raw=NULL;
    hd_receipt_set receipts;
    hd79_mount_roster r;
    hd79_mount_presence p;
    char epoch[25];
    size_t used=0,native=0;
    int rc,result=HD79_PRESENCE_STORE_FAILURE;
    if (!roster || !position || !valid_name(name)) return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if (!raw) return result;
    if (read_record(name,raw,&used,&native,&receipts) ||
        ((creature *)raw)->type!=PLAYER ||
        !native_name(((creature *)raw)->name,name) ||
        hd79_mount_authoritative_epoch(&receipts,epoch)) goto done;
    rc=hd79_presence_snapshot(&receipts,epoch,&r,&p);
    if (rc==1) result=HD79_PRESENCE_STORE_ABSENT;
    else if (rc==0) {
        *roster=r;
        *position=p;
        result=HD79_PRESENCE_STORE_OK;
    }
done:
    free(raw);
    return result;
}

static int hd79_presence_transaction(const char *name,
                                     const hd79_mount_roster *expected,
                                     const hd79_mount_presence *old_position,
                                     const hd79_mount_roster *desired,
                                     const hd79_mount_presence *new_position,
                                     hd79_mount_roster *out_roster,
                                     hd79_mount_presence *out_position)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set receipts;
    hd79_mount_roster prior,next,empty;
    hd79_mount_presence prior_p,next_p;
    char epoch[25], old_a[65],old_b[65],old_c[65];
    char new_a[65],new_b[65],new_c[65];
    size_t used=0,native=0,total=0;
    creature *disk;
    int lock=-1,ia,ib,ic,base,length,wr,rc;
    int result=HD79_PRESENCE_STORE_FAILURE;

    if (!out_roster || !out_position || !valid_name(name)) return result;
    if (!expected) {
        if (old_position || desired || new_position) return result;
    } else {
        if (!old_position || !desired || !new_position ||
            !hd79_presence_valid(expected,old_position) ||
            !hd79_presence_valid(desired,new_position) ||
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
    ia=hd79_mount_find(&receipts,hd79_mount_a_id);
    ib=hd79_mount_find(&receipts,hd79_mount_b_id);
    ic=hd79_mount_find(&receipts,HD79_MOUNT_PRESENCE_ID);

    if (!expected) {
        if (ic>=0) {
            /* Neither reinitialize a good record nor repair a corrupt one. */
            rc=hd79_presence_snapshot(&receipts,epoch,&prior,&prior_p);
            if (rc==0) result=HD79_PRESENCE_STORE_CONFLICT;
            goto done;
        }
        base=hd79_mount_pair(&receipts,epoch,&prior);
        if (base==0) {
            /* A truly EMPTY prior pair may safely acquire receipt 82. */
            if (prior.count || prior.active_id || ia<0 || ib<0)
                goto done;
            next=prior;
        } else if (base==1) {
            if (ia>=0 || ib>=0 ||
                hd79_mount_roster_new(&empty,epoch)!=1) goto done;
            next=empty;
        } else goto done;
        if (hd79_presence_new(&next,&next_p)!=1) goto done;
    } else {
        rc=hd79_presence_snapshot(&receipts,epoch,&prior,&prior_p);
        if (rc==1) {
            result=HD79_PRESENCE_STORE_CONFLICT;
            goto done;
        }
        if (rc!=0 || ia<0 || ib<0 || ic<0) goto done;
        if (hd79_mount_wire_encode(expected,old_a,old_b) ||
            hd79_presence_encode(expected,old_position,old_c)) goto done;
        if (strcmp(receipts.entries[ia].manifest_sha256,old_a) ||
            strcmp(receipts.entries[ib].manifest_sha256,old_b) ||
            strcmp(receipts.entries[ic].manifest_sha256,old_c)) {
            result=HD79_PRESENCE_STORE_CONFLICT;
            goto done;
        }
        next=*desired;
        next_p=*new_position;
    }
    if (hd79_mount_wire_encode(&next,new_a,new_b) ||
        hd79_presence_encode(&next,&next_p,new_c)) goto done;
    if (!expected) {
        if (base==1 &&
            (hd_receipt_add(&receipts,hd79_mount_a_id,new_a) ||
             hd_receipt_add(&receipts,hd79_mount_b_id,new_b))) goto done;
        if (hd_receipt_add(&receipts,HD79_MOUNT_PRESENCE_ID,new_c))
            goto done;
    } else {
        memcpy(receipts.entries[ia].manifest_sha256,new_a,65);
        memcpy(receipts.entries[ib].manifest_sha256,new_b,65);
        memcpy(receipts.entries[ic].manifest_sha256,new_c,65);
    }
    if (hd_receipt_encode(raw,HD_RAW_CAPACITY,native,&receipts,&total))
        goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,
                              (int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if (length<1 || length>(int)HD_PLAYER_COMPRESSED_LIMIT) goto done;
    wr=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)length);
    if (wr==HD_SNAPSHOT_OK || wr==HD_SNAPSHOT_UNCERTAIN) {
        *out_roster=next;
        *out_position=next_p;
        result=wr==HD_SNAPSHOT_OK ? HD79_PRESENCE_STORE_OK :
                                     HD79_PRESENCE_STORE_UNCERTAIN;
    }
done:
    if (lock>=0) { flock(lock,LOCK_UN); close(lock); }
    free(raw);
    free(packed);
    return result;
}
int hd79_presence_store_init(const char *name,
                             hd79_mount_roster *roster,
                             hd79_mount_presence *position)
{
    return hd79_presence_transaction(name,NULL,NULL,NULL,NULL,
                                     roster,position);
}
int hd79_presence_store_commit(const char *name,
                               const hd79_mount_roster *expected,
                               const hd79_mount_presence *expected_position,
                               const hd79_mount_roster *desired,
                               const hd79_mount_presence *desired_position,
                               hd79_mount_roster *out_roster,
                               hd79_mount_presence *out_position)
{
    if (!expected || !expected_position || !desired || !desired_position)
        return HD79_PRESENCE_STORE_FAILURE;
    return hd79_presence_transaction(name,expected,expected_position,
                                     desired,desired_position,
                                     out_roster,out_position);
}
