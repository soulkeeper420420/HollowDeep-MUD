#ifndef HD_ARMY_CORPSE_H
#define HD_ARMY_CORPSE_H

#include <stdint.h>

struct creature;

#define HD_ARMY_RAISE_TIMER 40
#define HD_ARMY_RAISE_COOLDOWN 120L

/* Captured before the native monster is freed. No live pointers or loot. */
typedef struct {
    char name[80];
    uint32_t experience;
    unsigned level, hp, mp;
    unsigned strength, dexterity, constitution, intelligence, piety;
    int unique;
} hd_army_corpse;

/* Preflight checks owner, mana, durable capacity and runtime space. The
 * commit receives the same record. A positive return means the summon is
 * durable and can be announced. An uncertain write must halt the private
 * gameplay process before control returns to the corpse handler. */
int hd_army_raise_ready(struct creature *owner, const hd_army_corpse *corpse);
int hd_army_raise_commit(struct creature *owner, const hd_army_corpse *corpse);

#endif
