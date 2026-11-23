/* Round79AD: one private, pure policy gate for six mount actions/travel.
 * There are NO command hooks, read-write player adapters, or I/O here.
 */
#include "hd79_ad_private_transitions.h"
#include <string.h>

int hd79_ad_private_plan_action(
    const hd79_mount_roster *prior,const hd79_mount_presence *where,
    unsigned action,unsigned id,unsigned native_room,
    int native_present,int stable_authorized,
    hd79_mount_roster *next,hd79_mount_presence *next_where)
{
    hd79_mount_roster state;
    hd79_mount_presence position;
    int rc;
    if(!next || !next_where || !hd79_presence_valid(prior,where) ||
       !native_room || native_room>HD79_PRESENCE_MAX_ROOM ||
       !id || id>prior->count ||
       (native_present!=0 && native_present!=1) ||
       (stable_authorized!=0 && stable_authorized!=1))
        return -1;
    switch(action) {
    case HD79_PRESENCE_BOARD:
        rc=hd79_mount_board(prior,&state,prior->epoch,id,native_present);
        break;
    case HD79_PRESENCE_DISMOUNT:
        if(id!=prior->active_id) return 0;
        rc=hd79_mount_dismount(prior,&state,prior->epoch);
        break;
    case HD79_PRESENCE_STABLE:
        rc=hd79_mount_stable(prior,&state,prior->epoch,id,native_room,
                             stable_authorized,native_present);
        break;
    case HD79_PRESENCE_RETRIEVE:
        rc=hd79_mount_retrieve(prior,&state,prior->epoch,id,native_room,
                               stable_authorized);
        break;
    default: return -1;
    }
    if(rc!=1) return rc==0?0:-1;
    rc=hd79_presence_step(prior,where,&state,action,id,native_room,
                          native_present,stable_authorized,&position);
    if(rc!=1) return rc==0?0:-1;
    *next=state;
    *next_where=position;
    return 1;
}

int hd79_ad_private_plan_mounted_move(
    const hd79_mount_roster *prior,const hd79_mount_presence *where,
    const hd_travel_plan *preview,unsigned player_breath,
    int native_move_succeeded,
    hd79_mount_roster *next,hd79_mount_presence *next_where,
    unsigned *next_player_breath)
{
    hd79_mount_roster state;
    hd79_mount_presence position;
    unsigned breath;
    int rc;
    if(!next || !next_where || !next_player_breath || !preview ||
       !hd79_presence_valid(prior,where) || !prior->active_id ||
       (native_move_succeeded!=0 && native_move_succeeded!=1))
        return -1;
    rc=hd79_mount_travel(prior,&state,prior->epoch,preview,player_breath,
                         native_move_succeeded,&breath);
    if(rc!=1) return rc==0?0:-1;
    position=*where;
    if(state.revision==prior->revision) {
        /* Safe retreat is FREE and requires no roster receipt write.
         * Passing this plan to the CAS writer would be invalid. */
        if(preview->destination_is_wilderness ||
           preview->resource!=HD_TRAVEL_FREE) return -1;
        *next=state;
        *next_where=position;
        *next_player_breath=breath;
        return 2;
    }
    if(state.revision!=prior->revision+1 ||
       preview->resource!=HD_TRAVEL_MOUNT_ENDURANCE ||
       !preview->destination_is_wilderness ||
       breath!=player_breath) return -1;
    position.revision=state.revision;
    if(!hd79_presence_valid(&state,&position)) return -1;
    *next=state;
    *next_where=position;
    *next_player_breath=breath;
    return 1;
}
