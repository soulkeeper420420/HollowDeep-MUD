/* Replacement for the private single-pet runtime in a disposable Army build. */
#include "mstruct.h"
#include "mextern.h"
#include "hd_necro_skeleton.h"
#include "hd_pet_store.h"
#include "hd_army_corpse.h"
#include "hd_army_restore.h"
#include "hd_corpse.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

extern int hd_store_is_necromancer(const char *);
extern int hd_roster_store_read(const char *, hd_pet_roster *);
extern int hd_roster_store_checkpoint(const char *, const hd_pet_roster *,
                                      const hd_pet_roster *, hd_pet_roster *);
extern int hd_roster_store_raise(const char *, const hd_pet_roster *,
                                const hd_roster_pet *, creature *, uint32_t,
                                long *, hd_pet_roster *);

typedef struct {
    creature *owner;
    hd_pet_roster saved;
    creature *pets[HD_ROSTER_CAP];
    long last_hit[HD_ROSTER_CAP];
} army_session;

static army_session sessions[PMAX];

static void storage_stop(const char *operation, int result)
{
    fprintf(stderr, "Undead Army private storage error at %s (%d)\n", operation, result);
    _exit(73);
}

static army_session *find_session(creature *owner)
{
    size_t i;
    if (!owner)
        return NULL;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner == owner)
            return &sessions[i];
    return NULL;
}

static army_session *find_pet(creature *pet, size_t *index)
{
    size_t i, j;
    if (!pet)
        return NULL;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner)
            for (j = 0; j < sessions[i].saved.count; ++j)
                if (sessions[i].pets[j] == pet) {
                    *index = j;
                    return &sessions[i];
                }
    return NULL;
}

static void checkpoint(army_session *session, const hd_pet_roster *requested)
{
    int rc = hd_roster_store_checkpoint(session->owner->name, &session->saved,
                                        requested, &session->saved);
    if (rc != HD_PET_OK)
        storage_stop("checkpoint", rc);
}

static void save_vitals(army_session *session)
{
    hd_pet_roster next = session->saved;
    size_t i;
    int dirty = 0;
    for (i = 0; i < next.count; ++i) {
        creature *pet = session->pets[i];
        hd_roster_pet *entry = &next.pets[i];
        if (!pet || pet->hpcur <= 0 || pet->mpcur < 0)
            storage_stop("invalid live pet", HD_PET_ERROR);
        if (pet->hpcur != entry->hpcur || pet->mpcur != entry->mpcur ||
            (pet->parent_rom && pet->rom_num != entry->room)) {
            dirty = 1;
            entry->hpcur = pet->hpcur;
            entry->mpcur = pet->mpcur;
            if (pet->parent_rom)
                entry->room = pet->rom_num;
        }
    }
    if (dirty)
        checkpoint(session, &next);
}

int hd_necro_skeleton_is_pet(creature *pet)
{
    size_t index;
    return find_pet(pet, &index) != NULL;
}

creature *hd_necro_skeleton_probe(creature *owner)
{
    army_session *session = find_session(owner);
    return session && session->saved.count ? session->pets[0] : NULL;
}

void hd_necro_skeleton_reconnect(creature *owner)
{
    size_t i;
    army_session *session;
    hd_pet_state legacy;
    int rc;
    if (!owner || owner->type != PLAYER || owner->class != MAGE ||
        !owner->parent_rom || find_session(owner) || !hd_store_is_necromancer(owner->name))
        return;
    for (i = 0; i < PMAX && sessions[i].owner; ++i)
        ;
    if (i == PMAX)
        storage_stop("session capacity", HD_PET_ERROR);
    session = &sessions[i];
    rc = hd_roster_store_read(owner->name, &session->saved);
    if (rc == HD_PET_ABSENT && hd_pet_store_init(owner->name, &legacy) == HD_PET_OK)
        rc = hd_roster_store_read(owner->name, &session->saved);
    if (rc != HD_PET_OK || hd_army_restore(&session->saved, session->pets))
        storage_stop("login", rc);
    session->owner = owner;
    for (i = 0; i < session->saved.count; ++i) {
        const hd_roster_pet *saved = &session->saved.pets[i];
        if (!saved->stay || saved->room == (unsigned)owner->rom_num)
            add_crt_rom(session->pets[i], owner->parent_rom, 0);
    }
    save_vitals(session);
}

static void detach(creature *pet)
{
    if (pet->parent_rom) {
        del_active(pet);
        del_crt_rom(pet, pet->parent_rom);
    }
}

void hd_necro_skeleton_logout(creature *owner)
{
    army_session *session = find_session(owner);
    size_t i;
    if (!session)
        return;
    save_vitals(session);
    session->owner = NULL;
    for (i = 0; i < session->saved.count; ++i) {
        detach(session->pets[i]);
        free_crt(session->pets[i]);
    }
    memset(session, 0, sizeof *session);
}

void hd_necro_skeleton_death(creature *pet)
{
    size_t index, remaining;
    army_session *session = find_pet(pet, &index);
    hd_pet_roster next;
    if (!session)
        storage_stop("unregistered death", HD_PET_ERROR);
    next = session->saved;
    --next.count;
    remaining = next.count - index;
    memmove(&next.pets[index], &next.pets[index + 1], remaining * sizeof next.pets[0]);
    checkpoint(session, &next);
    memmove(&session->pets[index], &session->pets[index + 1],
            remaining * sizeof session->pets[0]);
    memmove(&session->last_hit[index], &session->last_hit[index + 1],
            remaining * sizeof session->last_hit[0]);
    session->pets[next.count] = NULL;
    session->last_hit[next.count] = 0;
}

void hd_necro_skeleton_on_free(creature *who)
{
    size_t index;
    if (find_pet(who, &index))
        storage_stop("unexpected native pet free", HD_PET_ERROR);
    hd_necro_skeleton_logout(who);
}

void hd_necro_skeleton_follow(creature *owner, room *old_room, room *new_room)
{
    army_session *session = find_session(owner);
    size_t i;
    (void)old_room;
    if (!session || !new_room || owner->parent_rom != new_room)
        return;
    for (i = 0; i < session->saved.count; ++i) {
        creature *pet = session->pets[i];
        if (!session->saved.pets[i].stay && pet->parent_rom != new_room) {
            if (pet->parent_rom)
                del_crt_rom(pet, pet->parent_rom);
            add_crt_rom(pet, new_room, 0);
        }
    }
    save_vitals(session);
}

void hd_necro_skeleton_checkpoint_all(void)
{
    size_t i;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner)
            save_vitals(&sessions[i]);
}

void hd_necro_skeleton_tick(long now)
{
    size_t i;
    (void)now;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner)
            hd_necro_skeleton_follow(sessions[i].owner, NULL, sessions[i].owner->parent_rom);
}

void hd_necro_skeleton_room_unload(room *where)
{
    size_t i, j;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner) {
            save_vitals(&sessions[i]);
            for (j = 0; j < sessions[i].saved.count; ++j)
                if (sessions[i].pets[j]->parent_rom == where)
                    detach(sessions[i].pets[j]);
        }
}

void hd_necro_skeleton_room_load(room *where)
{
    size_t i, j;
    for (i = 0; i < PMAX; ++i)
        if (sessions[i].owner)
            for (j = 0; j < sessions[i].saved.count; ++j)
                if (!sessions[i].pets[j]->parent_rom &&
                    sessions[i].saved.pets[j].room == (unsigned)where->rom_num)
                    add_crt_rom(sessions[i].pets[j], where, 0);
}

int hd_necro_skeleton_can_heal(creature *owner)
{
    army_session *session = find_session(owner);
    size_t i;
    if (!session || !owner->parent_rom)
        return 0;
    for (i = 0; i < session->saved.count; ++i)
        if (session->pets[i]->parent_rom == owner->parent_rom)
            return 1;
    return 0;
}

void hd_necro_skeleton_assist(creature *owner, creature *target)
{
    army_session *session = find_session(owner);
    size_t i;
    long now;
    if (!session || !target || target->type != MONSTER || !owner->parent_rom ||
        owner->parent_rom != target->parent_rom || hd_necro_skeleton_is_pet(target) ||
        F_ISSET(target, MUNKIL) || F_ISSET(target, MMGONL) ||
        !is_enm_crt(owner->name, target))
        return;
    now = (long)time(NULL);
    for (i = 0; i < session->saved.count && target->hpcur > 1; ++i) {
        creature *pet = session->pets[i];
        int damage;
        if (pet->parent_rom != owner->parent_rom ||
            (session->last_hit[i] && now - session->last_hit[i] < 3))
            continue;
        session->last_hit[i] = now;
        damage = MIN(1 + pet->level / 8, target->hpcur - 1);
        target->hpcur -= (short)damage;
        add_enm_dmg(owner->name, target, damage);
    }
}

int hd_necro_raise(creature *owner, cmd *command)
{
    return hd_corpse_raise(owner, command);
}

int hd_necro_raise_or_action(creature *owner, cmd *command)
{
    if (command && command->num >= 2 &&
        (!strcmp(command->str[1], "corpse") || !strcmp(command->str[1], "skeleton")))
        return hd_corpse_raise(owner, command);
    return action(owner, command);
}

int hd_army_raise_ready(creature *owner, const hd_army_corpse *corpse)
{
    army_session *session = find_session(owner);
    if (!session) {
        print(owner->fd, "Only Necromancers can raise corpses.\n");
        return 0;
    }
    if (owner->mpcur < 8 || session->saved.count >= hd_roster_capacity(owner->level) ||
        !corpse->name[0] || session->saved.next_id == UINT32_MAX) {
        print(owner->fd, "You lack mana or room for another undead servant.\n");
        return 0;
    }
    return 1;
}

int hd_army_raise_commit(creature *owner, const hd_army_corpse *corpse)
{
    army_session *session = find_session(owner);
    hd_pet_roster preview;
    hd_roster_pet entry = {0};
    creature *materialized[HD_ROSTER_CAP];
    const unsigned char *ch;
    uint32_t identity = UINT32_C(2166136261);
    size_t index;
    int rc;
    long xp;

    if (!hd_army_raise_ready(owner, corpse))
        return 0;
    index = session->saved.count;
    /* Native corpses lack a template index. Keep the exact name separately;
     * the deterministic key is descriptive, while the roster ID is unique. */
    for (ch = (const unsigned char *)corpse->name; *ch; ++ch)
        identity = (identity ^ *ch) * UINT32_C(16777619);
    entry.template_id = identity ? identity : 1;
    memcpy(entry.name, corpse->name, sizeof entry.name);
    entry.unique = corpse->unique;
    entry.level = corpse->level;
    entry.room = owner->rom_num;
    entry.hpcur = entry.hpmax = corpse->hp;
    entry.mpcur = entry.mpmax = corpse->mp;
    entry.strength = corpse->strength;
    entry.dexterity = corpse->dexterity;
    entry.constitution = corpse->constitution;
    entry.intelligence = corpse->intelligence;
    entry.piety = corpse->piety;

    preview = session->saved;
    preview.count = 1;
    preview.pets[0] = entry;
    preview.pets[0].id = preview.next_id++;
    if (hd_army_restore(&preview, materialized))
        return 0;
    rc = hd_roster_store_raise(owner->name, &session->saved, &entry, owner,
                               corpse->experience, &xp, &session->saved);
    if (rc != HD_PET_OK) {
        free(materialized[0]);
        if (rc != HD_PET_ERROR)
            storage_stop("raise", rc);
        print(owner->fd, "The summon could not be saved.\n");
        return 0;
    }
    session->pets[index] = materialized[0];
    owner->mpcur -= 8;
    owner->experience = xp;
    add_crt_rom(session->pets[index], owner->parent_rom, 0);
    print(owner->fd, "You raise %s [pet %lu].\n", entry.name,
          (unsigned long)session->saved.pets[index].id);
    return 1;
}
