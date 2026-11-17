#ifndef HD_ARMY_RESTORE_H
#define HD_ARMY_RESTORE_H

#include "hd_pet_roster.h"

struct creature;

/* Build detached native creatures in saved roster order. On failure the
 * caller's array is unchanged. The caller owns the creatures on success
 * and must register their stable pet IDs before attaching them to rooms. */
int hd_army_restore(const hd_pet_roster *roster,
                    struct creature *pets[HD_ROSTER_CAP]);

#endif
