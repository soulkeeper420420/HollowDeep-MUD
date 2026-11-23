/* Round79AD R2: internal native owner/pointer/stable authority PRECHECK.
 * Zero writes and NO gameplay command caller; not a CAS/store adapter.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_verified_action.h"
#include "hd79_ad_private_transitions.h"
#include "hd79_mount_presence_store.h"
#include "hd79_mount_world_identity.h"
#include "hd79_stable_registry.h"

#define HD79_AD_OWNER_TAG_BOUND 2048U
static int owner_live_once(const creature *owner)
{
    const ctag *node;
    const room *world;
    unsigned steps=0,hits=0;
    if(!owner || owner->type!=PLAYER || owner->hpcur<=0 ||
       !owner->parent_rom || owner->rom_num<1 ||
       (unsigned)owner->rom_num>HD79_PRESENCE_MAX_ROOM ||
       !owner->name[0])return 0;
    world=owner->parent_rom;
    if(world->rom_num!=owner->rom_num)return 0;
    for(node=world->first_ply;node && steps<HD79_AD_OWNER_TAG_BOUND;
        node=node->next_tag,steps++) {
        if(node->crt==owner)hits++;
        if(hits>1)return 0;
    }
    return !node && hits==1;
}
int hd79_ad_verified_action_plan(creature *owner,unsigned action,unsigned id,
                                  const hd79_ad_death_receipt *proof,
                                  hd79_mount_roster *before,
                                  hd79_mount_presence *where,
                                  hd79_mount_roster *after,
                                  hd79_mount_presence *next_where)
{
    hd79_mount_roster state,next;
    hd79_mount_presence position,planned;
    unsigned room_id;
    int present=0,stable=0,result;
    unsigned name_len=0;
    if(!before||!where||!after||!next_where||!proof||
       !id||id>HD79_MOUNT_MAX_OWNED||
       (action!=HD79_PRESENCE_BOARD &&
        action!=HD79_PRESENCE_DISMOUNT &&
        action!=HD79_PRESENCE_STABLE &&
        action!=HD79_PRESENCE_RETRIEVE))return -1;
    if(!owner_live_once(owner))return 0;
    while(name_len<sizeof owner->name && owner->name[name_len])
        name_len++;
    if(!name_len || name_len==sizeof owner->name)return 0;
    room_id=(unsigned)owner->rom_num;
    if(hd79_presence_store_read(owner->name,&state,&position)!=
       HD79_PRESENCE_STORE_OK ||
       !hd79_presence_valid(&state,&position) ||
       id>state.count ||
       !hd79_ad_death_action_eligible(&state,proof,id))return 0;
    if(action==HD79_PRESENCE_BOARD || action==HD79_PRESENCE_STABLE) {
        /* This is the accepted exact pointer/epoch/room attestation.
         * No name-based monster lookup or player-supplied location. */
        present=hd79_world_mount_present(owner,id,&state,&position);
        if(present!=1)return 0;
    }
    if(action==HD79_PRESENCE_STABLE || action==HD79_PRESENCE_RETRIEVE) {
        /* Root-owned, hardcoded relative path in private cwd, verified by
         * the existing stable registry. Never a user-controlled path. */
        stable=hd79_stable_registry_check("hollowdeep-data",
                                          "mount-stables.hds",room_id);
        if(stable!=1)return 0;
    }
    result=hd79_ad_private_plan_action(&state,&position,action,id,room_id,
                                       present,stable,&next,&planned);
    if(result!=1)return result==0 ? 0:-1;
    /* Revalidate native owner and exact presence at completion of plan.
     * Future CAS adapter still MUST recheck epoch and room after save. */
    if(!owner_live_once(owner) || (unsigned)owner->rom_num!=room_id)
        return 0;
    if((action==HD79_PRESENCE_BOARD||action==HD79_PRESENCE_STABLE) &&
       hd79_world_mount_present(owner,id,&state,&position)!=1)
        return 0;
    *before=state;*where=position;*after=next;*next_where=planned;
    return 1;
}
