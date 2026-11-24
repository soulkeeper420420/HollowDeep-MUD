/* Round79AD R6B: unexposed, authenticated native four-receipt action CAS.
 * Source is included only into the disposable ELF32 player store with
 * HD79_AD_ACTION_CAS_PLAYTEST. This is NOT a player command/lifecycle API.
 * Caller MUST reconcile the native creature before exposing any action.
 */
#ifndef HD79_AD_FOUR_ACTION_STORE_H
#define HD79_AD_FOUR_ACTION_STORE_H
#include "hd79_ad_four_store.h"
struct creature;
/* All authority is recomputed from the live native owner and trusted
 * four-receipt player snapshot. No caller-supplied room, stable boolean,
 * presence boolean, death proof, or arbitrary proposed roster is accepted.
 * 0: atomic durable write; 2: stale/denied/no-op; 3: uncertain rename
 * (no mutation acknowledged, outputs untouched); -1: storage error.
 * Outputs are changed ONLY on 0. This function performs no NPC changes.
 */
int hd79_ad_four_action_commit_native(struct creature *owner,
                                      unsigned action,unsigned id,
                                      hd79_mount_roster *saved_roster,
                                      hd79_mount_presence *saved_presence,
                                      hd79_ad_death_receipt *saved_death);
#endif
