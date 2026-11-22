/* Round 79C: wilderness movement Breath (travel stamina), pure state rules.
 *
 * This is not oxygen/drowning and is unrelated to the existing PBRWAT flag.
 * Native movement and save hooks are intentionally NOT installed here.
 */
#ifndef HD_WILDERNESS_BREATH_H
#define HD_WILDERNESS_BREATH_H

#define HD_BREATH_MAX 100
#define HD_BREATH_WILDERNESS_MOVE_COST 2
#define HD_BREATH_TICK_RECOVERY 5
#define HD_BREATH_REST_RECOVERY 15

/* Apply before native movement: 1 allowed, 0 exhausted, -1 invalid. */
int hd_breath_can_move(int breath, int destination_is_wilderness);

/* Apply only AFTER confirmed successful movement; never on failed exits. */
int hd_breath_after_move(int breath, int destination_is_wilderness);

/* Apply once per VERIFIED native recovery tick (not on every command). */
int hd_breath_recover(int breath, int is_resting);

#endif
