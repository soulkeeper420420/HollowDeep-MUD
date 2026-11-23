/* Round79AD R2: unexposed fail-closed native action PRECHECK, not a command.
 * A future caller must load receipt #83 atomically from native player store,
 * and perform one CAS across 80/81/82/83 before any creature side effects.
 * This function performs zero writes and never enables mount gameplay.
 */
#ifndef HD79_AD_VERIFIED_ACTION_H
#define HD79_AD_VERIFIED_ACTION_H
#include "hd79_ad_death_receipt.h"
#include "hd79_mount_presence.h"
struct creature;
/* 1: internally verified and planned, 0: denied, -1: malformed.
 * Outputs are untouched unless 1. 'proof' is only a proposal from a
 * TRUSTED source: absent native #83 reader means no authorized caller.
 */
int hd79_ad_verified_action_plan(struct creature *owner,
                                  unsigned action,unsigned id,
                                  const hd79_ad_death_receipt *proof,
                                  hd79_mount_roster *before,
                                  hd79_mount_presence *where,
                                  hd79_mount_roster *after,
                                  hd79_mount_presence *next_where);
#endif
