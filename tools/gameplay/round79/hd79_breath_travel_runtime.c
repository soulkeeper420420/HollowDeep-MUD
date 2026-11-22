/* Round 79K: private native breathing and movement precommit logic.
 * No custom command bypasses the game's move()/go() exit restrictions.
 * No mounts, flight, stable or riding behavior are enabled here.
 */
#include "mextern.h"
#include "hd_breath_store.h"
#include "hd_breath_move_checkpoint.h"
#include "hd_wilderness_breath.h"
#include "hd79_breath_travel_runtime.h"
#include <stdint.h>
#include <time.h>
#include <string.h>

#define HD79_BREATH_PULSE_SECONDS 45U

/* Read an exact durable receipt; migrate unknown/legacy saves once.
 * Never overwrite an existing depleted or malformed receipt.
 */
static int hd79_ensure_breath(creature *owner,uint32_t now,
                               hd_breath_record *out)
{
    int result;
    if (!owner || !out || !now) return -1;
    result=hd_breath_store_read(owner->name,out);
    if (result==HD_BREATH_STORE_ABSENT) {
        result=hd_breath_store_init(owner->name,now,out);
        if (result==HD_BREATH_STORE_CONFLICT ||
            result==HD_BREATH_STORE_UNCERTAIN)
            result=hd_breath_store_read(owner->name,out);
    }
    return result==HD_BREATH_STORE_OK ? 0:-1;
}

/* If an injected writer fails after rename, read the two durable
 * components. The next native action is NOT approved unless the exact
 * expected new room and receipt revision are simultaneously present.
 * The atomic checkpoint guarantees they can never commit separately.
 */
static int hd79_confirm_uncertain(const char *name,int target,
                                  const hd_breath_record *expected)
{
    creature *persisted=NULL;
    hd_breath_record actual;
    int ok=0;
    if (!name || !expected) return -1;
    if (hd_store_load_player(name,&persisted)!=HD_STORE_OK ||
        !persisted) return -1;
    if (persisted->rom_num==target &&
        hd_breath_store_read(name,&actual)==HD_BREATH_STORE_OK &&
        actual.revision==expected->revision &&
        actual.current==expected->current &&
        !strcmp(actual.epoch,expected->epoch))
        ok=1;
    free_crt(persisted);
    return ok ? 0:-1;
}

int hd79_breath_status(creature *player,int *current)
{
    hd_breath_record state;
    time_t stamp;
    if (!player || !current || player->type!=PLAYER ||
        player->class>=CARETAKER) return -1;
    stamp=time((time_t *)0);
    if (stamp<=0 || (unsigned long)stamp>UINT32_MAX ||
        hd79_ensure_breath(player,(uint32_t)stamp,&state))
        return -1;
    *current=(int)state.current;
    return 0;
}

int hd79_breath_precommit(creature *player,room *destination)
{
    hd_breath_record before,after;
    creature proposed;
    uint32_t now;
    time_t stamp;
    int wilderness,rc;

    if (!player || !destination || !player->parent_rom)
        return -1;
    /* NPCs and existing immortal/admin tools retain native logic. */
    if (player->type!=PLAYER || player->class>=CARETAKER)
        return 0;
    if (destination==player->parent_rom ||
        destination->rom_num==player->rom_num)
        return -1;
    stamp=time((time_t *)0);
    if (stamp<=0 || (unsigned long)stamp>UINT32_MAX) return -1;
    now=(uint32_t)stamp;

    wilderness=hd79_wilderness_tile(destination->rom_num);
    if (wilderness<0) {
        print(player->fd,"Wilderness map data is unavailable. Travel denied.\n");
        return -1;
    }
    if (hd79_ensure_breath(player,now,&before)) {
        print(player->fd,"Your Breath record cannot be verified. Travel denied.\n");
        return -1;
    }
    if (hd_breath_can_move((int)before.current,wilderness)<=0) {
        print(player->fd,"You are too exhausted to continue through the wilderness. Rest or retreat.\n");
        return -1;
    }

    /* Create a temporary on-disk candidate; leave the live player in
     * the source room until the combined save is acknowledged.
     * This prevents a failed save from producing a free movement.
     */
    proposed=*player;
    proposed.rom_num=destination->rom_num;
    proposed.parent_rom=destination;
    rc=hd_breath_store_checkpoint_move(
         player->name,&proposed,player->rom_num,&before,
         wilderness,now,&after);
    if (rc==HD_BREATH_STORE_UNCERTAIN) {
        if (!hd79_confirm_uncertain(player->name,destination->rom_num,
                                    &after))
            rc=HD_BREATH_STORE_OK;
    }
    if (rc!=HD_BREATH_STORE_OK) {
        print(player->fd,
              "Travel was not confirmed by the save system. "
              "Reconnect before trying again.\n");
        return -1;
    }
    return 0;
}

int hd79_breath_pulse(creature *player,long tick)
{
    hd_breath_record before,after;
    uint32_t now;
    int rc;
    if (!player || player->type!=PLAYER ||
        player->class>=CARETAKER || tick<=0 ||
        (unsigned long)tick>UINT32_MAX)
        return 0;
    now=(uint32_t)tick;
    rc=hd_breath_store_read(player->name,&before);
    if (rc!=HD_BREATH_STORE_OK ||
        before.current>=HD_BREATH_MAX ||
        now<=before.last_recover ||
        now-before.last_recover<HD79_BREATH_PULSE_SECONDS)
        return 0;
    /* Only a native periodic update with elapsed wall time can
     * regenerate Breath; typing rest repeatedly has no effect.
     * +15 resting is pending verified native rest-state parsing.
     */
    rc=hd_breath_store_step(player->name,&before,HD_BREATH_OP_RECOVER,
                            0,0,now,&after);
    return rc==HD_BREATH_STORE_OK ? 0:-1;
}
