/* Round 79K: private native pre-room-change Breath game hook.
 * Integrates the atomic room+Breath co-checkpoint at the real native
 * destination-validated boundary. All changes are feature-gated.
 */
#ifndef HD79_BREATH_TRAVEL_RUNTIME_H
#define HD79_BREATH_TRAVEL_RUNTIME_H

/* Return 0 to permit the original native move/go transfer, -1 to deny.
 * Called only after all vanilla exit restrictions and destination room
 * capacity checks have passed, before leaving-room announcements, room
 * mutation, follower movement or traps. Never call for denied exits.
 */
int hd79_breath_precommit(creature *, room *);

/* Called only from existing update_ply native update callback.
 * Limits recovery to the player's durable last_recover, never to
 * repeated input. Returns 0 on no-op or committed recovery.
 */
int hd79_breath_pulse(creature *, long);

/* Return 1 for an exact valid wilderness.map tile id, 0 for ordinary
 * room numbers, -1 for inaccessible/invalid reserved wilderness IDs.
 */
int hd79_wilderness_tile(int);
#endif
