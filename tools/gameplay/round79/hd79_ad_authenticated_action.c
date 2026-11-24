/* Round79AD R6A: native authenticated, READ-ONLY action planning.
 * R2 accepted proposed #83 from its caller, while R3 added the durable
 * four-record native reader. This replaces the untrusted proof with the
 * actual atomic player receipt, and makes no game or player mutation.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_authenticated_action.h"
#include "hd79_ad_private_transitions.h"
#include "hd79_mount_world_identity.h"
#include "hd79_stable_registry.h"

#define HD79_R6A_OWNER_LIST_BOUND 2048U
static int native_owner_exactly_once(const creature *owner)
{
    const room *r;
    const ctag *tag;
    unsigned steps=0,hits=0,n=0;
    if(!owner||owner->type!=PLAYER||owner->hpcur<=0||
       !owner->parent_rom||owner->rom_num<1||
       (unsigned)owner->rom_num>HD79_PRESENCE_MAX_ROOM)return 0;
    while(n<sizeof owner->name && owner->name[n])++n;
    if(!n || n==sizeof owner->name)return 0;
    r=owner->parent_rom;
    if(r->rom_num!=owner->rom_num)return 0;
    for(tag=r->first_ply;tag && steps<HD79_R6A_OWNER_LIST_BOUND;
        tag=tag->next_tag,steps++) {
        if(tag->crt==owner)++hits;
        if(hits>1)return 0;
    }
    return !tag && hits==1;
}
int hd79_ad_authenticated_action_plan(creature *owner,unsigned action,
                                       unsigned id,hd79_mount_roster *before,
                                       hd79_mount_presence *where,
                                       hd79_ad_death_receipt *death,
                                       hd79_mount_roster *after,
                                       hd79_mount_presence *next_where)
{
    hd79_mount_roster r,next;
    hd79_mount_presence p,np;
    hd79_ad_death_receipt d;
    unsigned room_id;
    int present=0,stable=0,rc;
    if(!before||!where||!death||!after||!next_where||
       !id||id>HD79_MOUNT_MAX_OWNED||
       (action!=HD79_PRESENCE_BOARD &&
        action!=HD79_PRESENCE_DISMOUNT &&
        action!=HD79_PRESENCE_STABLE &&
        action!=HD79_PRESENCE_RETRIEVE))return -1;
    if(!native_owner_exactly_once(owner))return 0;
    room_id=(unsigned)owner->rom_num;
    /* Unlike R2, #83 proof comes exclusively from the authenticated
     * native compressed snapshot. Missing/partial/forged #83 denies. */
    if(hd79_ad_four_store_read(owner->name,&r,&p,&d)!=HD79_AD_FOUR_OK||
       !hd79_presence_valid(&r,&p)||
       !hd79_ad_death_valid(&r,&d)||
       !hd79_ad_death_action_eligible(&r,&d,id))return 0;
    if(action==HD79_PRESENCE_BOARD||action==HD79_PRESENCE_STABLE) {
        present=hd79_world_mount_present(owner,id,&r,&p);
        if(present!=1)return 0;
    }
    if(action==HD79_PRESENCE_STABLE||action==HD79_PRESENCE_RETRIEVE) {
        stable=hd79_stable_registry_check("hollowdeep-data",
                                          "mount-stables.hds",room_id);
        if(stable!=1)return 0;
    }
    rc=hd79_ad_private_plan_action(&r,&p,action,id,room_id,
                                   present,stable,&next,&np);
    if(rc!=1)return rc==0?0:-1;
    /* No trust can be carried across a room/owner change, even in a
     * single process. Future CAS must separately recheck under lock. */
    if(!native_owner_exactly_once(owner)||
       (unsigned)owner->rom_num!=room_id)return 0;
    if((action==HD79_PRESENCE_BOARD||action==HD79_PRESENCE_STABLE)&&
       hd79_world_mount_present(owner,id,&r,&p)!=1)return 0;
    if(!native_owner_exactly_once(owner)||
       (unsigned)owner->rom_num!=room_id)return 0;
    /* R3 #83 and the native planner must agree with all new revisions. */
    if(!hd79_presence_valid(&next,&np)||
       !hd79_ad_death_valid(&r,&d)||
       next.revision!=r.revision+1U)return -1;
    *before=r;*where=p;*death=d;*after=next;*next_where=np;
    return 1;
}
