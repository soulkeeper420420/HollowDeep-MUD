/* Round79AD R6A: read-only native four-receipt action preview.
 * It authenticates #83 from the native compressed PLAYERPATH record;
 * does not trust a caller-provided death proof. No commands, saves,
 * creature mutation, travel, or restoration are installed.
 */
#ifndef HD79_AD_AUTHENTICATED_ACTION_H
#define HD79_AD_AUTHENTICATED_ACTION_H
#include "hd79_ad_four_store.h"
struct creature;
/* 1 = exact verified preview, 0 = unavailable/denied, -1 = malformed.
 * All outputs untouched unless 1. The returned prior death record is
 * the one read from the native player store. It is NOT a login proof.
 * A future write must recheck ALL FOUR canonical receipts under lock.
 */
int hd79_ad_authenticated_action_plan(struct creature *owner,
                                       unsigned action,unsigned id,
                                       hd79_mount_roster *before,
                                       hd79_mount_presence *where,
                                       hd79_ad_death_receipt *death,
                                       hd79_mount_roster *after,
                                       hd79_mount_presence *next_where);
#endif
