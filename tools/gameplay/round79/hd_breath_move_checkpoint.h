/* Round 79J - PRIVATE native atomic room + Breath co-checkpoint.
 *
 * Storage only. This function does not itself call move/go, resolve exits,
 * decide wilderness membership, recover or update the live room graph.
 * The caller must reconcile an uncertain write and roll back in-memory
 * movement upon a rejected checkpoint before it is safe to enable gameplay.
 */
#ifndef HD_BREATH_MOVE_CHECKPOINT_H
#define HD_BREATH_MOVE_CHECKPOINT_H

#include "hd_breath_store.h"

/* After a verified successful movement, pass the NEW live player state,
 * the OLD durable room, and the expected Breath receipt read before moving.
 * Under the original player directory lock:
 *   - old saved room must match expected_previous_room,
 *   - saved receipt must match the supplied epoch/revision exactly,
 *   - player room AND updated Breath receipt are written in one snapshot.
 * destination_is_wilderness: 1 only if validated in wilderness.map.
 * Returning to an ordinary room charges zero, even when exhausted.
 *
 * On OK / UNCERTAIN, next_receipt contains the candidate state.
 * On FAILURE / CONFLICT it is not written. If UNCERTAIN, re-read BOTH
 * player room and Breath receipt before admitting further movement.
 */
int hd_breath_store_checkpoint_move(
    const char *name, creature *moved_player,
    int expected_previous_room, const hd_breath_record *expected_receipt,
    int destination_is_wilderness, uint32_t now,
    hd_breath_record *next_receipt);
#endif
