/* Round79AD: UNEXPOSED private six-species mount NPC placeholders.
 * No character-facing command, persistence award, template permission,
 * automatic login rehydration, riding, stable or movement activation.
 * These are 1-HP noncombat test creatures, NOT gameplay-balanced mounts.
 */
#ifndef HD79_AD_PRIVATE_FLEET_H
#define HD79_AD_PRIVATE_FLEET_H
#include "hd79_mount_presence_store.h"
struct creature;

/* One trusted, no-player-input, temporary native NPC for an already-owned
 * and physically recorded mount. Source of authority is disk receipts
 * 80/81/82 and the *actual native room list*. 1=bound, 0=denied, -1=error.
 * Output pointer is changed only on success. No save is written.
 */
int hd79_ad_private_spawn(struct creature *owner, unsigned mount_id,
                          struct creature **out);

/* Reconnect replay is disabled until durable mount-death tombstones exist.
 * Always zero, regardless of roster/player arguments. */
int hd79_ad_private_reconnect_allowed(void);

/* Trusted internal label only; never a player-selected monster template. */
const char *hd79_ad_private_species_name(int species);
#endif
