/* Round79AD R6B: private PLAYERPATH locked CAS for native mount actions.
 * Included AFTER the R3 four-store implementation inside hd_player_store.c.
 * No global command, lifecycle, login, movement or reward hook calls this.
 * R6C must coordinate physical mount appearance/absence with this commit.
 */
#ifndef HD79_AD_ACTION_CAS_PLAYTEST
#error "R6B private four-receipt action CAS requires explicit feature gate"
#endif
#ifndef HD79_AD_FOUR_STORE_PLAYTEST
#error "R6B native action CAS requires R3 atomic four-receipt store"
#endif
#include "hd79_ad_four_action_store.h"
#include "hd79_ad_authenticated_action.h"
#include "hd79_ad_private_transitions.h"

/* Compare all four canonical wires, never compiler-specific struct padding. */
static int hd79_ad_action_same_four(const hd79_mount_roster *a,
                                    const hd79_mount_presence *ap,
                                    const hd79_ad_death_receipt *ad,
                                    const hd79_mount_roster *b,
                                    const hd79_mount_presence *bp,
                                    const hd79_ad_death_receipt *bd)
{
    char a0[65],a1[65],a2[65],a3[65];
    char b0[65],b1[65],b2[65],b3[65];
    if(hd79_mount_wire_encode(a,a0,a1) ||
       hd79_mount_wire_encode(b,b0,b1) ||
       hd79_presence_encode(a,ap,a2) ||
       hd79_presence_encode(b,bp,b2) ||
       hd79_ad_death_wire_encode(a,ad,a3) ||
       hd79_ad_death_wire_encode(b,bd,b3))return 0;
    return !strcmp(a0,b0) && !strcmp(a1,b1) &&
           !strcmp(a2,b2) && !strcmp(a3,b3);
}

int hd79_ad_four_action_commit_native(creature *owner,
                                      unsigned action,unsigned id,
                                      hd79_mount_roster *saved_roster,
                                      hd79_mount_presence *saved_presence,
                                      hd79_ad_death_receipt *saved_death)
{
    hd79_mount_roster before,preview,locked,desired,check_before,check_next;
    hd79_mount_presence oldp,planned,lockedp,desiredp,check_p,check_np;
    hd79_ad_death_receipt death,lockedd,check_d;
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set set;
    char epoch[25],a0[65],a1[65],a2[65],a3[65];
    char name[sizeof owner->name];
    unsigned room_id,chars=0;
    size_t used=0,native=0,total=0;
    int lock=-1,ia,ib,ic,ix,wr,length,rc=HD79_AD_FOUR_FAILURE;
    int present,stable,step;
    creature *disk;

    if(!owner || !saved_roster || !saved_presence || !saved_death ||
       !id || id>HD79_MOUNT_MAX_OWNED ||
       (action!=HD79_PRESENCE_BOARD &&
        action!=HD79_PRESENCE_DISMOUNT &&
        action!=HD79_PRESENCE_STABLE &&
        action!=HD79_PRESENCE_RETRIEVE))return HD79_AD_FOUR_FAILURE;
    if(hd79_ad_authenticated_action_plan(owner,action,id,&before,&oldp,&death,
                                          &preview,&planned)!=1)
        return HD79_AD_FOUR_CONFLICT;
    room_id=(unsigned)owner->rom_num;
    while(chars<sizeof owner->name && owner->name[chars])++chars;
    if(!chars || chars==sizeof owner->name)return HD79_AD_FOUR_CONFLICT;
    memcpy(name,owner->name,chars);
    name[chars]=0;
    if(!valid_name(name) || !hd79_ad_death_action_eligible(&before,&death,id))
        return HD79_AD_FOUR_CONFLICT;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if(!raw || !packed)goto done;
    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(lock<0 || flock(lock,LOCK_EX)<0 ||
       read_record(name,raw,&used,&native,&set))goto done;
    disk=(creature *)raw;
    if(disk->type!=PLAYER || disk->level<1 || disk->level>60 ||
       !native_name(disk->name,name) ||
       hd79_mount_authoritative_epoch(&set,epoch))goto done;
    if(hd79_ad_four_snapshot(&set,epoch,&locked,&lockedp,&lockedd)!=0 ||
       !hd79_ad_four_matches(&set,&before,&oldp,&death) ||
       !hd79_ad_action_same_four(&before,&oldp,&death,
                                 &locked,&lockedp,&lockedd) ||
       !hd79_ad_death_action_eligible(&locked,&lockedd,id)){
        rc=HD79_AD_FOUR_CONFLICT;
        goto done;
    }
    /* Never trust a boolean or location from command text: R6A has
     * verified the bound native pointer and root-owned stable registry.
     * Repeat that *native* verification while the player lock is held. */
    if(hd79_ad_authenticated_action_plan(owner,action,id,
                  &check_before,&check_p,&check_d,&check_next,&check_np)!=1 ||
       owner->rom_num<1 || (unsigned)owner->rom_num!=room_id ||
       strcmp(name,owner->name) ||
       !hd79_ad_action_same_four(&locked,&lockedp,&lockedd,
                                 &check_before,&check_p,&check_d) ||
       !hd79_ad_action_same_four(&preview,&planned,&death,
                                 &check_next,&check_np,&check_d)){
        rc=HD79_AD_FOUR_CONFLICT;
        goto done;
    }
    present=(action==HD79_PRESENCE_BOARD || action==HD79_PRESENCE_STABLE);
    stable=(action==HD79_PRESENCE_STABLE || action==HD79_PRESENCE_RETRIEVE);
    step=hd79_ad_private_plan_action(&locked,&lockedp,action,id,room_id,
                                    present,stable,&desired,&desiredp);
    if(step!=1 ||
       !hd79_ad_action_same_four(&preview,&planned,&death,
                                 &desired,&desiredp,&lockedd)){
        rc=HD79_AD_FOUR_CONFLICT;
        goto done;
    }
    if(hd79_mount_wire_encode(&desired,a0,a1) ||
       hd79_presence_encode(&desired,&desiredp,a2) ||
       hd79_ad_death_wire_encode(&desired,&lockedd,a3))goto done;
    ia=hd79_mount_find(&set,hd79_mount_a_id);
    ib=hd79_mount_find(&set,hd79_mount_b_id);
    ic=hd79_mount_find(&set,HD79_MOUNT_PRESENCE_ID);
    ix=hd79_mount_find(&set,HD79_AD_DEATH_RECEIPT_ID);
    if(ia<0 || ib<0 || ic<0 || ix<0)goto done;
    memcpy(set.entries[ia].manifest_sha256,a0,65);
    memcpy(set.entries[ib].manifest_sha256,a1,65);
    memcpy(set.entries[ic].manifest_sha256,a2,65);
    memcpy(set.entries[ix].manifest_sha256,a3,65);
    if(hd_receipt_encode(raw,HD_RAW_CAPACITY,native,&set,&total))goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,
                               (int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if(length<1 || length>(int)HD_PLAYER_COMPRESSED_LIMIT)goto done;
    wr=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)length);
    if(wr==HD_SNAPSHOT_OK){
        *saved_roster=desired;
        *saved_presence=desiredp;
        *saved_death=lockedd;
        rc=HD79_AD_FOUR_OK;
    }else if(wr==HD_SNAPSHOT_UNCERTAIN){
        /* NEVER acknowledge a possibly committed save as success.
         * The caller must reconnect, read all four canonical receipts,
         * and must not repeat this action or change the native creature.
         * A stale retry cannot pass the revision/CAS check. */
        rc=HD79_AD_FOUR_UNCERTAIN;
    }
done:
    if(lock>=0){flock(lock,LOCK_UN);close(lock);}
    free(raw);
    free(packed);
    return rc;
}
