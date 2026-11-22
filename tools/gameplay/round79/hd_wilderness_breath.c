/* Round 79C: bounded deterministic Breath travel-stamina policy.
 * No creature struct access, no world mutation, no player save writes.
 */
#include "hd_wilderness_breath.h"

static int valid_breath(int breath)
{
    return breath >= 0 && breath <= HD_BREATH_MAX;
}

int hd_breath_can_move(int breath, int destination_is_wilderness)
{
    if (!valid_breath(breath) ||
        (destination_is_wilderness != 0 && destination_is_wilderness != 1))
        return -1;
    /* Safe retreat into towns and interior areas is ALWAYS allowed. */
    if (!destination_is_wilderness)
        return 1;
    return breath >= HD_BREATH_WILDERNESS_MOVE_COST;
}

int hd_breath_after_move(int breath, int destination_is_wilderness)
{
    int allowed = hd_breath_can_move(breath,destination_is_wilderness);
    if (allowed < 0 || allowed == 0)
        return -1;
    return destination_is_wilderness ?
        breath - HD_BREATH_WILDERNESS_MOVE_COST : breath;
}

int hd_breath_recover(int breath, int is_resting)
{
    int recovered;
    if (!valid_breath(breath) || (is_resting != 0 && is_resting != 1))
        return -1;
    recovered = is_resting ?
        HD_BREATH_REST_RECOVERY : HD_BREATH_TICK_RECOVERY;
    /* Max - breath prevents overflow even on a native ELF32 build. */
    if (recovered >= HD_BREATH_MAX - breath)
        return HD_BREATH_MAX;
    return breath + recovered;
}
