/* Round 79H: includes the tested Round 79F Breath record rules.
 * Must be included only inside native hd_player_store.c, with its
 * locked read_record()/hd_atomic_player_snapshot() infrastructure.
 * This does NOT hook actual movement or player heartbeat.
 */
#ifndef HD_PET_STORE_PLAYTEST
#error "Breath receipt transactions require verified pet atomic player store"
#endif
#include "hd_breath_store.h"
#include "hd_wilderness_breath.c"
#include "hd_breath_record.c"

/* Unique fixed reserved HDTR1 receipt ID, distinct from 74..78. */
static int hd_breath_entry(const hd_receipt_set *receipts)
{
    size_t i;
    if (!receipts) return -1;
    for (i=0;i<receipts->count;++i)
        if (!strcmp(receipts->entries[i].claim_id,breath_id))
            return (int)i;
    return -1;
}

/* A read does not create or recover Breath. All getters fail closed.
 * On success, output is only assigned after the checksum-verified
 * compressed player record and Breath wire have been fully checked.
 */
int hd_breath_store_read(const char *name,hd_breath_record *out)
{
    unsigned char *raw;
    hd_receipt_set receipts;
    size_t size=0,native=0;
    int idx,result=HD_BREATH_STORE_FAILURE;
    hd_breath_record state;
    if (!out || !valid_name(name)) return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if (!raw) return result;
    if (!read_record(name,raw,&size,&native,&receipts) &&
        ((creature *)raw)->type==PLAYER) {
        idx=hd_breath_entry(&receipts);
        if (idx<0)
            result=HD_BREATH_STORE_ABSENT;
        else if (!hd_breath_record_decode(
                     receipts.entries[idx].manifest_sha256,&state)) {
            *out=state;
            result=HD_BREATH_STORE_OK;
        }
    }
    free(raw);
    return result;
}

static int hd_breath_store_transaction(
    const char *name,const hd_breath_record *expected,
    unsigned action,int wilderness,int resting,uint32_t now,
    hd_breath_record *out)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set receipts;
    hd_breath_record prior,next;
    char wire[65],before[65],epoch[25];
    size_t used=0,native=0,total=0;
    int lock=-1,idx=-1,length,result=HD_BREATH_STORE_FAILURE,wr;
    creature *owner;
    if (!out || !valid_name(name) || !now) return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;

    /* The existing directory lock serializes all ordinary saves,
     * old/new Breath writes, Conjure and pet roster transactions. */
    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (lock<0 || flock(lock,LOCK_EX)<0 ||
        read_record(name,raw,&used,&native,&receipts))
        goto done;

    owner=(creature *)raw;
    if (owner->type!=PLAYER || owner->level<1 || owner->level>60)
        goto done;

    idx=hd_breath_entry(&receipts);
    if (action==0U) { /* One-time legacy/new-character migration */
        if (expected) goto done;
        if (idx>=0) {
            if (!hd_breath_record_decode(
                  receipts.entries[idx].manifest_sha256,out))
                result=HD_BREATH_STORE_CONFLICT;
            goto done;
        }
        if (pet_epoch(epoch) ||
            hd_breath_record_new(&next,epoch,now)) goto done;
    } else {
        if (!expected || idx<0) {
            result=HD_BREATH_STORE_CONFLICT;
            goto done;
        }
        if (hd_breath_record_decode(
                receipts.entries[idx].manifest_sha256,&prior) ||
            hd_breath_record_encode(expected,before))
            goto done;
        if (strcmp(before,receipts.entries[idx].manifest_sha256)) {
            result=HD_BREATH_STORE_CONFLICT;
            goto done;
        }
        if (hd_breath_record_step(&prior,&next,action,wilderness,
                                  resting,now))
            goto done;
        /* Indoor retreat is free and does not modify the receipt. */
        if (next.revision==prior.revision) {
            *out=prior;
            result=HD_BREATH_STORE_OK;
            goto done;
        }
    }

    if (hd_breath_record_encode(&next,wire)) goto done;
    if (idx<0) {
        if (hd_receipt_add(&receipts,breath_id,wire)) goto done;
    } else
        memcpy(receipts.entries[idx].manifest_sha256,wire,65);

    if (hd_receipt_encode(raw,HD_RAW_CAPACITY,native,
                          &receipts,&total)) goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,
                               (int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if (length<1 || length>HD_PLAYER_COMPRESSED_LIMIT) goto done;

    wr=hd_atomic_player_snapshot(
        PLAYERPATH,name,packed,(size_t)length);
    if (wr==HD_SNAPSHOT_OK || wr==HD_SNAPSHOT_UNCERTAIN) {
        *out=next;
        result=wr==HD_SNAPSHOT_OK ? HD_BREATH_STORE_OK :
                                     HD_BREATH_STORE_UNCERTAIN;
    }
done:
    if (lock>=0) { flock(lock,LOCK_UN); close(lock); }
    free(raw);
    free(packed);
    return result;
}

int hd_breath_store_init(const char *name,uint32_t now,hd_breath_record *out)
{
    return hd_breath_store_transaction(name,NULL,0U,0,0,now,out);
}

int hd_breath_store_step(const char *name,
    const hd_breath_record *expected,unsigned action,
    int wilderness,int resting,uint32_t now,hd_breath_record *out)
{
    if (action!=HD_BREATH_OP_TRAVEL && action!=HD_BREATH_OP_RECOVER)
        return HD_BREATH_STORE_FAILURE;
    return hd_breath_store_transaction(
        name,expected,action,wilderness,resting,now,out);
}
