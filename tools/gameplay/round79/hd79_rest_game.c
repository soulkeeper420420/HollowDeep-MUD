/* Round79P: PRIVATE native explicit rest integration.
 * 512 bounded transient session slots. Never serializes game pointers,
 * adds to creature/room ABI, changes social actions, or modifies mounts.
 * All non-read-only commands interrupt rest before native execution.
 * Free/death hooks clear slots; changing room or being damaged also
 * denies the accelerated Breath rate.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_rest_session.h"
#include "hd79_rest_game.h"
#include <stdint.h>
#include <string.h>
#include <time.h>

#define HD79_REST_SLOTS 512
#define HD79_REST_NAME_BYTES 80

typedef struct hd79_rest_slot {
    creature *owner;
    int fd,room_id,initial_hp;
    char name[HD79_REST_NAME_BYTES];
    hd79_rest_session session;
} hd79_rest_slot;

static hd79_rest_slot hd79_slots[HD79_REST_SLOTS];

static void hd79_slot_clear(hd79_rest_slot *slot)
{
    if (slot) memset(slot,0,sizeof *slot);
}
static int hd79_identity_matches(const hd79_rest_slot *slot,
                                 creature *player)
{
    if (!slot || !player || slot->owner!=player) return 0;
    return slot->fd==player->fd &&
           slot->room_id==player->rom_num &&
           !strcmp(slot->name,player->name);
}
static hd79_rest_slot *hd79_find(creature *player)
{
    unsigned i;
    for(i=0;i<HD79_REST_SLOTS;i++) {
        hd79_rest_slot *slot=&hd79_slots[i];
        if (slot->owner!=player) continue;
        if (!hd79_identity_matches(slot,player)) {
            hd79_slot_clear(slot);
            return NULL;
        }
        return slot;
    }
    return NULL;
}
void hd79_rest_forget(creature *player)
{
    unsigned i;
    if (!player) return;
    for(i=0;i<HD79_REST_SLOTS;i++)
        if (hd79_slots[i].owner==player)
            hd79_slot_clear(&hd79_slots[i]);
}
static int hd79_rest_begin(creature *player,uint32_t now)
{
    hd79_rest_slot *slot;
    unsigned i;
    if (!player || !player->name[0] || !now ||
        strlen(player->name)>=HD79_REST_NAME_BYTES ||
        player->type!=PLAYER || player->class>=CARETAKER ||
        !player->parent_rom || player->hpcur<=0)
        return -1;
    slot=hd79_find(player);
    if (!slot) {
        for(i=0;i<HD79_REST_SLOTS;i++)
            if (!hd79_slots[i].owner) {
                slot=&hd79_slots[i];
                break;
            }
    }
    if (!slot) return -1; /* bounded: never evict another player */
    if (!slot->owner) {
        memset(slot,0,sizeof *slot);
        slot->owner=player;
        slot->fd=player->fd;
        slot->room_id=player->rom_num;
        slot->initial_hp=player->hpcur;
        strcpy(slot->name,player->name);
        hd79_rest_session_init(&slot->session);
    }
    return hd79_rest_session_begin(&slot->session,now);
}
#ifdef HD79_REST_TESTING
int hd79_rest_begin_at_for_test(creature *player,uint32_t now)
{
    return hd79_rest_begin(player,now);
}
#endif
int hd79_rest_command(creature *player,cmd *command)
{
    time_t current;
    int already;
    hd79_rest_slot *slot;
    (void)command;
    if (!player || player->type!=PLAYER || player->class>=CARETAKER ||
        !player->parent_rom || player->hpcur<=0) {
        if (player) print(player->fd,"You cannot rest right now.\n");
        return 0;
    }
    current=time((time_t *)0);
    if (current<=0 || (unsigned long)current>UINT32_MAX) {
        print(player->fd,"Rest is unavailable while the clock is invalid.\n");
        return 0;
    }
    slot=hd79_find(player);
    already=slot && slot->session.active;
    if (hd79_rest_begin(player,(uint32_t)current)<0) {
        print(player->fd,"There is no safe resting session available.\n");
        return 0;
    }
    if (already)
        print(player->fd,"You are already resting. Remain still.\n");
    else
        print(player->fd,"You settle down to rest. Remain still for the Breath bonus.\n");
    return 0;
}
void hd79_rest_before_command(creature *player,const char *word)
{
    if (!player || !word) return;
    /* Only proven read-only informational commands may retain rest.
     * Other commands, including existing sleep/sit/stand social actions,
     * movement, combat, spellcasts, save and quit, interrupt first.
     */
    if (!strcmp(word,"rest") || !strcmp(word,"look") ||
        !strcmp(word,"l") || !strcmp(word,"help") ||
        !strcmp(word,"skills"))
        return;
    hd79_rest_forget(player);
}
int hd79_rest_bonus_eligible(creature *player,uint32_t now,
                              uint32_t durable_last_recover)
{
    hd79_rest_slot *slot;
    if (!player || player->hpcur<=0) return 0;
    slot=hd79_find(player);
    if (!slot) return 0;
    /* Room relocation and HP loss are independent interruption
     * conditions, even if a caller bypassed normal command routing.
     * No stale rest state survives a mismatched player identity.
     */
    if (player->hpcur<slot->initial_hp) {
        hd79_rest_forget(player);
        return 0;
    }
    return hd79_rest_session_eligible(&slot->session,now,
                                      durable_last_recover);
}
