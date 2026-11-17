/* One raised skeleton per Necromancer, stats captured from a verified kill.
 * Private playtest only. In-memory lifetime has NO time expiry.
 * Never write a summoned monster into room or player binary records.
 */
#include "mstruct.h"
#include "mextern.h"
#include "hd_necro_skeleton.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef HD_NECROMANCER_PLAYTEST
#error "Skeleton skill may only be built inside the Necromancer playtest"
#endif

extern int hd_store_is_necromancer(const char *name);
#define HD_NECRO_MP_COST 8

typedef struct {
    creature *owner;
    creature *pet;
    char owner_name[80];
    short corpse_hp, corpse_mp;
    short corpse_level;
    short corpse_room;
    int corpse_ready;
    long last_hit;
} necro_pet_slot;
static necro_pet_slot pets[PMAX];

static necro_pet_slot *slot_for_owner(creature *owner)
{
    int i;
    if (!owner || owner->type != PLAYER || !owner->name[0]) return NULL;
    for (i = 0; i < PMAX; ++i) {
        if (pets[i].owner == owner) return &pets[i];
        if (!pets[i].owner && pets[i].owner_name[0] &&
            !strcmp(pets[i].owner_name, owner->name)) return &pets[i];
    }
    return NULL;
}
static necro_pet_slot *free_slot(void)
{
    int i;
    for (i = 0; i < PMAX; ++i)
        if (!pets[i].owner && !pets[i].pet && !pets[i].owner_name[0])
            return &pets[i];
    return NULL;
}
static void forget_pet(necro_pet_slot *slot)
{
    if (!slot) return;
    slot->pet = NULL;
    slot->last_hit = 0;
    if (!slot->corpse_ready) memset(slot, 0, sizeof *slot);
}

int hd_necro_skeleton_is_pet(creature *who)
{
    int i;
    if (!who) return 0;
    for (i = 0; i < PMAX; ++i)
        if (pets[i].pet == who) return 1;
    return 0;
}
struct creature *hd_necro_skeleton_probe(creature *owner)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    return slot ? slot->pet : NULL;
}
/* The death hook runs only on a REAL killed monster with a real player killer.
 * Copy the stats, not the dying monster pointer, and bind to the kill room.
 */
void hd_necro_skeleton_record_kill(creature *victim, creature *killer)
{
    necro_pet_slot *slot;
    if (!victim || !killer || victim->type != MONSTER ||
        killer->type != PLAYER || killer->class != MAGE ||
        killer->fd < 0 || !killer->parent_rom ||
        victim->parent_rom != killer->parent_rom ||
        victim->hpmax < 1 || victim->mpmax < 0 ||
        F_ISSET(victim, MUNKIL) || hd_necro_skeleton_is_pet(victim) ||
        !hd_store_is_necromancer(killer->name)) return;
    slot = slot_for_owner(killer);
    if (!slot) slot = free_slot();
    if (!slot) return;
    slot->owner = killer;
    strcpy(slot->owner_name, killer->name);
    slot->corpse_hp = victim->hpmax;
    slot->corpse_mp = victim->mpmax;
    slot->corpse_level = (short)((victim->level > 0 && victim->level <= 60) ? victim->level : 1);
    slot->corpse_room = killer->rom_num;
    slot->corpse_ready = 1;
}
int hd_necro_raise(creature *owner, cmd *cmnd)
{
    necro_pet_slot *slot;
    creature *pet;
    if (!owner || !cmnd || owner->type != PLAYER || owner->fd < 0 ||
        !owner->parent_rom) return 0;
    if (owner->class != MAGE || !hd_store_is_necromancer(owner->name)) {
        print(owner->fd, "Only Necromancers can raise skeletons.\n");
        return 0;
    }
    if (!((cmnd->num == 2 && !strcmp(cmnd->str[1], "skeleton")) ||
          (cmnd->num == 1 && !strcmp(cmnd->str[0], "raiseskeleton")))) {
        print(owner->fd, "Usage: raise skeleton\n"); return 0;
    }
    slot = slot_for_owner(owner);
    if (slot && slot->pet) {
        print(owner->fd, "You already command a skeleton.\n"); return 0;
    }
    if (!slot || !slot->corpse_ready || slot->corpse_room != owner->rom_num) {
        print(owner->fd, "Slay a monster here before raising its skeleton.\n");
        return 0;
    }
    if (owner->mpcur < HD_NECRO_MP_COST) {
        print(owner->fd, "You need 8 mana to raise a skeleton.\n"); return 0;
    }
    pet = calloc(1, sizeof *pet);
    if (!pet) { print(owner->fd, "Your magic falters.\n"); return 0; }
    strcpy(pet->name, "skeleton servant");
    strcpy(pet->description, "A skeletal servant raised from a fallen monster.");
    pet->type = MONSTER;
    pet->class = FIGHTER;
    pet->fd = -1;
    pet->level = (char)slot->corpse_level;
    pet->hpmax = slot->corpse_hp;
    pet->hpcur = pet->hpmax;
    pet->mpmax = slot->corpse_mp;
    pet->mpcur = pet->mpmax;
    pet->strength = pet->dexterity = 10;
    pet->ndice = 1;
    pet->sdice = 2;
    pet->experience = 0;
    pet->gold = 0;
    /* Zero-value summon: no XP, gold, equipment, quests or chest credit. */
    F_SET(pet, MNRGLD);
    slot->owner = owner;
    slot->pet = pet;
    slot->corpse_ready = 0; /* Cannot raise the same slain monster twice. */
    slot->last_hit = 0;
    owner->mpcur -= HD_NECRO_MP_COST;
    add_crt_rom(pet, owner->parent_rom, 1);
    print(owner->fd, "You raise a skeleton (%d HP / %d MP).\n",
          (int)pet->hpmax, (int)pet->mpmax);
    return 0;
}
int hd_necro_raise_or_action(creature *owner, cmd *cmnd)
{
    if (cmnd && cmnd->num == 2 && !strcmp(cmnd->str[1], "skeleton"))
        return hd_necro_raise(owner, cmnd);
    return action(owner, cmnd);
}
/* The native healing spells already target room monsters, including the pet.
 * Exposing this predicate allows targeted potions without allowing arbitrary
 * monster potion feeds or bypassing other item restrictions.
 */
int hd_necro_skeleton_can_heal(creature *healer)
{
    necro_pet_slot *slot = slot_for_owner(healer);
    return slot && slot->pet && slot->pet->hpcur > 0 &&
        healer->fd >= 0 && healer->parent_rom &&
        slot->pet->parent_rom == healer->parent_rom &&
        healer->class == MAGE && hd_store_is_necromancer(healer->name);
}
void hd_necro_skeleton_assist(creature *owner, creature *target)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    int damage;
    long now;
    if (!slot || !slot->pet || !owner || !target ||
        owner->type != PLAYER || target->type != MONSTER ||
        slot->pet == target || !owner->parent_rom ||
        target->parent_rom != owner->parent_rom ||
        slot->pet->parent_rom != owner->parent_rom ||
        slot->pet->hpcur < 1 || target->hpcur < 2 ||
        F_ISSET(target, MUNKIL) || F_ISSET(target, MMGONL) ||
        !is_enm_crt(owner->name, target)) return;
    now = (long)time(NULL);
    if (slot->last_hit && now - slot->last_hit < 3) return;
    slot->last_hit = now;
    damage = 1 + slot->pet->level / 8;
    if (damage >= target->hpcur) damage = target->hpcur - 1;
    if (damage < 1) return;
    target->hpcur -= (short)damage;
    add_enm_dmg(owner->name, target, damage);
    print(owner->fd, "Your skeleton strikes for %d damage.\n", damage);
}
void hd_necro_skeleton_follow(creature *owner, room *old_room, room *new_room)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    if (!slot || !slot->pet || !old_room || !new_room ||
        old_room == new_room || slot->pet->parent_rom != old_room ||
        !owner || owner->parent_rom != new_room || slot->pet->hpcur < 1) return;
    del_crt_rom(slot->pet, old_room);
    add_crt_rom(slot->pet, new_room, 1);
}
void hd_necro_skeleton_tick(long now)
{
    int i;
    (void)now; /* No expiry: summoned minions remain until actually killed. */
    for (i = 0; i < PMAX; ++i) {
        necro_pet_slot *slot = &pets[i];
        if (!slot->pet) continue;
        if (slot->pet->hpcur < 1 || !slot->pet->parent_rom) {
            /* The native death/free path clears the registry. */
            continue;
        }
        if (slot->owner && slot->owner->parent_rom &&
            slot->pet->parent_rom != slot->owner->parent_rom)
            hd_necro_skeleton_follow(slot->owner, slot->pet->parent_rom,
                                     slot->owner->parent_rom);
    }
}
/* Leave the skeleton in the world across disconnects in the same process. */
void hd_necro_skeleton_logout(creature *owner)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    if (slot) slot->owner = NULL;
}
void hd_necro_skeleton_reconnect(creature *owner)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    if (!slot || !slot->owner_name[0] || !owner ||
        !hd_store_is_necromancer(owner->name)) return;
    slot->owner = owner;
    if (slot->pet && owner->parent_rom && slot->pet->parent_rom &&
        owner->parent_rom != slot->pet->parent_rom)
        hd_necro_skeleton_follow(owner, slot->pet->parent_rom,
                                 owner->parent_rom);
}
void hd_necro_skeleton_on_free(creature *who)
{
    int i;
    if (!who) return;
    for (i = 0; i < PMAX; ++i) {
        necro_pet_slot *slot = &pets[i];
        if (slot->pet == who) { forget_pet(slot); return; }
        if (slot->owner == who) { slot->owner = NULL; return; }
    }
}
