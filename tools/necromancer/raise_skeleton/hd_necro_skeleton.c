/* A single temporary, non-lootable skeleton. Private playtest only. */
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

/* Persistent Necromancer identity is verified against the native save trailer. */
extern int hd_store_is_necromancer(const char *name);

#define HD_NECRO_LIFETIME 120L
#define HD_NECRO_MP_COST 8
#define HD_NECRO_MIN_LEVEL 1

typedef struct {
    creature *owner;
    creature *pet;
    long until;
    long last_hit;
} necro_pet_slot;
static necro_pet_slot pets[PMAX];

static necro_pet_slot *slot_for_owner(creature *owner)
{
    int i;
    for (i = 0; i < PMAX; ++i)
        if (pets[i].owner == owner && owner != NULL) return &pets[i];
    return NULL;
}
static necro_pet_slot *free_slot(void)
{
    int i;
    for (i = 0; i < PMAX; ++i)
        if (!pets[i].owner && !pets[i].pet) return &pets[i];
    return NULL;
}
static void release_slot(necro_pet_slot *slot)
{
    creature *pet;
    if (!slot) return;
    pet = slot->pet;
    memset(slot, 0, sizeof *slot);
    if (!pet) return;
    if (pet->parent_rom) del_crt_rom(pet, pet->parent_rom);
    free_crt(pet);
}
struct creature *hd_necro_skeleton_probe(creature *owner)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    return slot ? slot->pet : NULL;
}
int hd_necro_raise(creature *owner, cmd *cmnd)
{
    necro_pet_slot *slot;
    creature *pet;
    long now;
    int level;
    if (!owner || !cmnd || owner->type != PLAYER || owner->fd < 0 ||
        !owner->parent_rom) return 0;
    if (owner->class != MAGE || !hd_store_is_necromancer(owner->name)) {
        print(owner->fd, "Only Necromancers can raise skeletons.\n");
        return 0;
    }
    if (!((cmnd->num == 2 && !strcmp(cmnd->str[1], "skeleton")) ||
          (cmnd->num == 1 && !strcmp(cmnd->str[0], "raiseskeleton")))) {
        print(owner->fd, "Usage: raise skeleton\n");
        return 0;
    }
    now = (long)time(NULL);
    slot = slot_for_owner(owner);
    if (slot && slot->until <= now) { release_slot(slot); slot = NULL; }
    if (slot) { print(owner->fd, "You already command a skeleton.\n"); return 0; }
    if (owner->level < HD_NECRO_MIN_LEVEL || owner->mpcur < HD_NECRO_MP_COST) {
        print(owner->fd, "You need 8 mana to raise a skeleton.\n"); return 0;
    }
    slot = free_slot();
    if (!slot) { print(owner->fd, "The necromantic wards are occupied.\n"); return 0; }
    pet = calloc(1, sizeof *pet);
    if (!pet) { print(owner->fd, "Your magic falters.\n"); return 0; }
    strcpy(pet->name, "a skeletal servant");
    strcpy(pet->description, "A temporary skeletal servant bound to its summoner.");
    pet->type = MONSTER;
    pet->class = FIGHTER;
    pet->fd = -1;
    level = owner->level;
    if (level > 10) level = 10;
    pet->level = level;
    pet->hpmax = (short)(8 + level * 2);
    pet->hpcur = pet->hpmax;
    pet->strength = pet->dexterity = 10;
    pet->ndice = 1;
    pet->sdice = 2;
    pet->experience = 0;
    pet->gold = 0;
    /* Never grant loot/XP when a skeleton is killed. */
    F_SET(pet, MNRGLD);
    owner->mpcur -= HD_NECRO_MP_COST;
    slot->owner = owner;
    slot->pet = pet;
    slot->until = now + HD_NECRO_LIFETIME;
    slot->last_hit = 0;
    add_crt_rom(pet, owner->parent_rom, 1);
    print(owner->fd, "You raise a skeletal servant for two minutes.\n");
    return 0;
}
int hd_necro_raise_or_action(creature *owner, cmd *cmnd)
{
    if (cmnd && cmnd->num == 2 && !strcmp(cmnd->str[1], "skeleton"))
        return hd_necro_raise(owner, cmnd);
    return action(owner, cmnd);
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
        target->hpcur < 2 || F_ISSET(target, MUNKIL) ||
        F_ISSET(target, MMGONL) ||
        !is_enm_crt(owner->name, target)) return;
    now = (long)time(NULL);
    if (now >= slot->until) { release_slot(slot); return; }
    if (slot->last_hit && now - slot->last_hit < 3) return;
    slot->last_hit = now;
    damage = 1 + slot->pet->level / 8;
    if (damage >= target->hpcur) damage = target->hpcur - 1;
    if (damage < 1) return;
    target->hpcur -= (short)damage;
    /* No independent kill or XP reward. Credit damage to the real player. */
    add_enm_dmg(owner->name, target, damage);
    print(owner->fd, "Your skeleton strikes for %d damage.\n", damage);
}
void hd_necro_skeleton_follow(creature *owner, room *old_room, room *new_room)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    if (!slot || !slot->pet || !old_room || !new_room ||
        old_room == new_room || slot->pet->parent_rom != old_room ||
        !owner || owner->parent_rom != new_room) return;
    del_crt_rom(slot->pet, old_room);
    add_crt_rom(slot->pet, new_room, 1);
}
void hd_necro_skeleton_tick(long now)
{
    int i;
    for (i = 0; i < PMAX; ++i) {
        necro_pet_slot *slot = &pets[i];
        if (!slot->pet) continue;
        if (!slot->owner || !slot->owner->parent_rom ||
            !slot->pet->parent_rom || now >= slot->until) {
            release_slot(slot);
            continue;
        }
        if (slot->pet->parent_rom != slot->owner->parent_rom)
            hd_necro_skeleton_follow(slot->owner, slot->pet->parent_rom,
                                     slot->owner->parent_rom);
    }
}
void hd_necro_skeleton_logout(creature *owner)
{
    necro_pet_slot *slot = slot_for_owner(owner);
    if (slot) release_slot(slot);
}
void hd_necro_skeleton_on_free(creature *who)
{
    int i;
    if (!who) return;
    for (i = 0; i < PMAX; ++i) {
        necro_pet_slot *slot = &pets[i];
        if (slot->pet == who) { memset(slot, 0, sizeof *slot); return; }
        if (slot->owner == who) { release_slot(slot); return; }
    }
}
