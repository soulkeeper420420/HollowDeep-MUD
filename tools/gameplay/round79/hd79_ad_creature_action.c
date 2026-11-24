/* Round79AD R6C private physical lifecycle bridge.
 * R6A verifies player+live native pointer+stable authority; R6B commits
 * 80/81/82/83 atomically. Never mutate a native NPC before durable success.
 * A failed/unknown receipt must not produce a success message or respawn.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_creature_action.h"
#include "hd79_ad_authenticated_action.h"
#include "hd79_ad_four_action_store.h"
#include "hd79_ad_private_fleet.h"
#include "hd79_mount_world_identity.h"
#include "hd79_mount_wire.h"
#include <string.h>

#define HD79_R6C_TAG_LIMIT 2048U
static int same_four(const hd79_mount_roster *a,const hd79_mount_presence *ap,
                     const hd79_ad_death_receipt *ad,
                     const hd79_mount_roster *b,const hd79_mount_presence *bp,
                     const hd79_ad_death_receipt *bd)
{
    char a0[65],a1[65],a2[65],a3[65],b0[65],b1[65],b2[65],b3[65];
    if(hd79_mount_wire_encode(a,a0,a1) ||
       hd79_mount_wire_encode(b,b0,b1) ||
       hd79_presence_encode(a,ap,a2) ||
       hd79_presence_encode(b,bp,b2) ||
       hd79_ad_death_wire_encode(a,ad,a3) ||
       hd79_ad_death_wire_encode(b,bd,b3))return 0;
    return !strcmp(a0,b0) && !strcmp(a1,b1) &&
           !strcmp(a2,b2) && !strcmp(a3,b3);
}
/* Read-only exact pointer membership; no potentially freed pointer access. */
static int pointer_in_room(const room *world,const creature *mount)
{
    const ctag *t;
    unsigned count=0,steps=0;
    if(!world||!mount)return -1;
    for(t=world->first_mon;t && steps<HD79_R6C_TAG_LIMIT;
        t=t->next_tag,steps++) {
        if(t->crt==mount)++count;
        if(count>1)return -1;
    }
    return t ? -1:(int)count;
}
int hd79_ad_creature_action(creature *owner,unsigned action,unsigned id)
{
    hd79_mount_roster before,after,written,disk;
    hd79_mount_presence where,next_where,written_where,disk_where;
    hd79_ad_death_receipt death,written_death,disk_death;
    creature *native=NULL,*new_mount=NULL;
    room *home;
    unsigned room_id;
    int rc,found;
    if(!owner || id<1 || id>HD79_MOUNT_MAX_OWNED ||
       (action!=HD79_PRESENCE_BOARD && action!=HD79_PRESENCE_DISMOUNT &&
        action!=HD79_PRESENCE_STABLE && action!=HD79_PRESENCE_RETRIEVE))
        return HD79_AD_CREATURE_INVALID;
    if(hd79_ad_authenticated_action_plan(owner,action,id,
            &before,&where,&death,&after,&next_where)!=1)
        return HD79_AD_CREATURE_DENIED;
    room_id=(unsigned)owner->rom_num;
    home=owner->parent_rom;
    if(!home||home->rom_num!=owner->rom_num)return HD79_AD_CREATURE_DENIED;
    if(action==HD79_PRESENCE_BOARD||action==HD79_PRESENCE_STABLE){
        native=hd79_ad_native_bound_creature(owner,id,&before,&where);
        if(!native || pointer_in_room(home,native)!=1)
            return HD79_AD_CREATURE_DENIED;
    }
    rc=hd79_ad_four_action_commit_native(owner,action,id,
                                         &written,&written_where,&written_death);
    if(rc!=HD79_AD_FOUR_OK && rc!=HD79_AD_FOUR_UNCERTAIN)
        return rc==HD79_AD_FOUR_CONFLICT ? HD79_AD_CREATURE_DENIED:
               HD79_AD_CREATURE_PENDING;
    /* Never infer success from an uncertain rename return code. Read back
     * ALL FOUR wires, including original death serial and monotone mask. */
    if(hd79_ad_four_store_read(owner->name,&disk,&disk_where,&disk_death)!=
            HD79_AD_FOUR_OK ||
       !same_four(&after,&next_where,&death,&disk,&disk_where,&disk_death))
        return HD79_AD_CREATURE_PENDING;
    if(rc==HD79_AD_FOUR_OK &&
       !same_four(&written,&written_where,&written_death,
                  &after,&next_where,&death))
        return HD79_AD_CREATURE_PENDING;
    if(owner->parent_rom!=home || (unsigned)owner->rom_num!=room_id ||
       home->rom_num!=(int)room_id)
        return HD79_AD_CREATURE_PENDING;
    if(native){
        /* Old identity remains valid until the actual del_crt_rom hook.
         * R5 unregisters the pointer on removal and gates combat death. */
        if(hd79_ad_native_bound_creature(owner,id,&before,&where)!=native ||
           pointer_in_room(home,native)!=1 || native->hpcur<=0)
            return HD79_AD_CREATURE_PENDING;
        del_crt_rom(native,home);
        found=pointer_in_room(home,native);
        if(found!=0)return HD79_AD_CREATURE_PENDING;
        free_crt(native);
        if(hd79_ad_native_bound_creature(owner,id,&before,&where))
            return HD79_AD_CREATURE_PENDING;
    } else {
        /* Dismount/retrieve only instantiate a living, durably recorded
         * owned species, through the R5 strict #83 + world bind constructor.
         * If allocation/binding fails, no success may be acknowledged. */
        if(hd79_ad_private_spawn(owner,id,&new_mount)!=1 ||
           !new_mount ||
           hd79_world_mount_present(owner,id,&disk,&disk_where)!=1)
            return HD79_AD_CREATURE_PENDING;
    }
    return HD79_AD_CREATURE_COMPLETE;
}
