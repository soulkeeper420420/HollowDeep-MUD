#include "mstruct.h"
#include "hd_army_restore.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int hd_army_restore(const hd_pet_roster *roster, creature *pets[HD_ROSTER_CAP])
{
    creature *staged[HD_ROSTER_CAP] = {0};
    unsigned char wire[HD_ROSTER_WIRE_MAX];
    size_t i;

    if (!pets || !hd_roster_encode(roster, wire, sizeof wire))
        return -1;
    for (i = 0; i < roster->count; ++i) {
        const hd_roster_pet *saved = &roster->pets[i];
        creature *pet = calloc(1, sizeof *pet);
        int has_identity = saved->name[0] != 0;
        if (!pet) {
            while (i)
                free(staged[--i]);
            return -1;
        }
        staged[i] = pet;
        if (has_identity) {
            strcpy(pet->name, saved->name);
            snprintf(pet->description, sizeof pet->description, "%s undead servant.",
                     saved->unique ? "A unique" : "An");
        } else {
            strcpy(pet->name, saved->template_id ? "undead servant" : "skeleton servant");
            strcpy(pet->description, "A servant raised from a fallen monster.");
        }
        pet->type = MONSTER;
        pet->class = FIGHTER;
        pet->fd = -1;
        pet->level = (char)saved->level;
        pet->rom_num = (short)saved->room;
        pet->hpmax = (short)saved->hpmax;
        pet->hpcur = (short)saved->hpcur;
        pet->mpmax = (short)saved->mpmax;
        pet->mpcur = (short)saved->mpcur;
        pet->strength = has_identity ? (char)saved->strength : 10;
        pet->dexterity = has_identity ? (char)saved->dexterity : 10;
        pet->constitution = (char)saved->constitution;
        pet->intelligence = (char)saved->intelligence;
        pet->piety = (char)saved->piety;
        pet->ndice = 1;
        pet->sdice = 2;
        /* Pet XP is kept in the roster. Native creature XP is kill value. */
        F_SET(pet, MNRGLD);
    }
    memcpy(pets, staged, sizeof staged);
    return 0;
}
