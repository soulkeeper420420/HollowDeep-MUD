/* Included after the tested Breath store in hd_player_store.c. */
#include "hd79_mount_store.h"
#include "hd79_mount_roster.c"
#include "hd79_mount_wire.c"
#include "hd_mount_travel.c"

static int mount_pair(const hd_receipt_set *set, const char *epoch,
                      hd79_mount_roster *out, int indexes[2])
{
    size_t i;
    indexes[0]=indexes[1]=-1;
    for (i=0;i<set->count;++i) {
        if (!strcmp(set->entries[i].claim_id,mount_first_id)) indexes[0]=(int)i;
        if (!strcmp(set->entries[i].claim_id,mount_second_id)) indexes[1]=(int)i;
    }
    if (indexes[0]<0 && indexes[1]<0)
        return hd79_mount_roster_new(out,epoch)==1 ? HD79_MOUNT_ABSENT : HD79_MOUNT_ERROR;
    if (indexes[0]<0 || indexes[1]<0 ||
        hd79_mount_wire_decode(set->entries[indexes[0]].manifest_sha256,
                               set->entries[indexes[1]].manifest_sha256,out) ||
        strcmp(epoch,out->epoch)) return HD79_MOUNT_ERROR;
    return HD79_MOUNT_OK;
}

int hd79_mount_read(const char *name, hd79_mount_roster *out)
{
    unsigned char *raw;
    hd_receipt_set set;
    hd_breath_record breath;
    hd79_mount_roster state;
    size_t size,native;
    int rc=HD79_MOUNT_ERROR,idx,pair[2];
    if (!out || !valid_name(name)) return rc;
    raw=malloc(HD_RAW_CAPACITY);
    if (!raw) return rc;
    if (!read_record(name,raw,&size,&native,&set) && ((creature *)raw)->type==PLAYER) {
        idx=hd_breath_entry(&set);
        if (idx>=0 && !hd_breath_record_decode(set.entries[idx].manifest_sha256,&breath)) {
            rc=mount_pair(&set,breath.epoch,&state,pair);
            if (rc>=0) *out=state;
        }
    }
    free(raw);
    return rc;
}

/* Only the native command and validated movement boundary may call this.
 * Full paired CAS and the live character snapshot share one directory lock. */
int hd79_mount_change(creature *owner, const hd79_mount_roster *expected,
    unsigned action,unsigned argument,unsigned stable,int wilderness,
    const hd_travel_plan *plan,hd79_mount_roster *out)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set set;
    hd_breath_record breath;
    hd79_mount_roster old,next;
    creature snapshot,*disk;
    otag worn[MAXWEAR];
    char a[65],b[65],old_a[65],old_b[65];
    size_t used,native,total,required;
    int lock=-1,idx,pair[2],rc,result=HD79_MOUNT_ERROR,slot,length,wr,serialized;
    unsigned id=0,next_breath;
    long price=0;
    if (!owner || !expected || !out || owner->type!=PLAYER || !valid_name(owner->name) ||
        !owner->parent_rom || owner->rom_num!=owner->parent_rom->rom_num ||
        hd79_mount_wire_encode(expected,old_a,old_b)) return result;
    snapshot=*owner;
    for (slot=0;slot<MAXWEAR;++slot) {
        if (!snapshot.ready[slot]) continue;
        worn[slot].obj=snapshot.ready[slot];
        worn[slot].next_tag=snapshot.first_obj;
        snapshot.first_obj=&worn[slot];
        snapshot.ready[slot]=NULL;
    }
    raw=malloc(HD_RAW_CAPACITY);
    packed=malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;
    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (lock<0 || flock(lock,LOCK_EX) ||
        read_record(owner->name,raw,&used,&native,&set)) goto done;
    disk=(creature *)raw;
    if (disk->type!=PLAYER || disk->rom_num!=owner->rom_num) {
        result=HD79_MOUNT_CONFLICT; goto done;
    }
    idx=hd_breath_entry(&set);
    if (idx<0 || hd_breath_record_decode(set.entries[idx].manifest_sha256,&breath)) goto done;
    rc=mount_pair(&set,breath.epoch,&old,pair);
    if (rc<0 || hd79_mount_wire_encode(&old,a,b)) goto done;
    if (strcmp(a,old_a) || strcmp(b,old_b)) { result=HD79_MOUNT_CONFLICT; goto done; }
    if (action==HD79_MOUNT_BUY) {
        if (!hd79_mount_stable_room(owner->rom_num) || argument<1 || argument>6) goto done;
        price=100L*argument;
        if (owner->gold<price || disk->gold!=owner->gold) goto done;
        rc=hd79_mount_award(&old,&next,breath.epoch,(int)argument,&id);
    } else if (action==HD79_MOUNT_BOARD)
        rc=hd79_mount_board(&old,&next,breath.epoch,argument,1);
    else if (action==HD79_MOUNT_OFF)
        rc=hd79_mount_dismount(&old,&next,breath.epoch);
    else if (action==HD79_MOUNT_DEPOSIT)
        rc=hd79_mount_stable(&old,&next,breath.epoch,argument,stable,
             stable==(unsigned)owner->rom_num && hd79_mount_stable_room(owner->rom_num),1);
    else if (action==HD79_MOUNT_RETRIEVE)
        rc=hd79_mount_retrieve(&old,&next,breath.epoch,argument,stable,
             stable==(unsigned)owner->rom_num && hd79_mount_stable_room(owner->rom_num));
    else if (action==HD79_MOUNT_MOVE) {
        if (!plan || !old.active_id || argument>=RMAX ||
            (int)argument==owner->rom_num || hd79_wilderness_tile((int)argument)!=wilderness)
            goto done;
        rc=hd79_mount_travel(&old,&next,breath.epoch,plan,breath.current,1,&next_breath);
        if (rc==1 && next_breath!=breath.current) goto done;
        snapshot.rom_num=(short)argument;
    } else goto done;
    if (rc!=1) goto done;
    if (hd79_mount_wire_encode(&next,a,b)) goto done;
    if (pair[0]<0) {
        if (set.count>HD_RECEIPT_MAX-2 ||
            hd_receipt_add(&set,mount_first_id,a) || hd_receipt_add(&set,mount_second_id,b)) goto done;
    } else {
        memcpy(set.entries[pair[0]].manifest_sha256,a,65);
        memcpy(set.entries[pair[1]].manifest_sha256,b,65);
    }
    snapshot.gold-=price;
    if (native_size(&snapshot,&required)) goto done;
    serialized=write_crt_to_mem((char *)raw,&snapshot,0);
    if (serialized<0 || (size_t)serialized!=required ||
        hd_receipt_encode(raw,HD_RAW_CAPACITY,required,&set,&total)) goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,(int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if (length<1) goto done;
    wr=hd_atomic_player_snapshot(PLAYERPATH,owner->name,packed,(size_t)length);
    if (wr==HD_SNAPSHOT_OK || wr==HD_SNAPSHOT_UNCERTAIN) {
        *out=next;
        result=wr==HD_SNAPSHOT_OK ? HD79_MOUNT_OK : HD79_MOUNT_UNCERTAIN;
    }
done:
    if (lock>=0) { flock(lock,LOCK_UN); close(lock); }
    free(raw); free(packed);
    return result;
}
