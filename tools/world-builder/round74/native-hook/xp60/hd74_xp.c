/* Round 74B private XP integration. No native structure or player-save mutation. */
#include "hd74_xp.h"
#include "hd74_progression.h"
#include <stdint.h>

static const hd74_rules hd74_xp_rules = {60,1000,50,3,18,50,3,180,2,10};

long hd74_xp_for_level(int level)
{
    uint32_t threshold = 0;
    if (level < 1 || level > HD74_LEVEL_CAP ||
        hd74_exp_threshold(&hd74_xp_rules,(unsigned)level,&threshold) != HD74_OK)
        return -1L;
    return (long)threshold;
}
long hd74_xp_for_next(int current_level)
{
    if (current_level < 1 || current_level >= HD74_LEVEL_CAP) return -1L;
    return hd74_xp_for_level(current_level+1);
}
int hd74_level_from_xp(long xp)
{
    int level;
    if (xp <= 0L) return 1;
    if (xp > HD74_XP_MAX) xp = HD74_XP_MAX;
    for (level=2; level<=HD74_LEVEL_CAP; ++level) {
        long need = hd74_xp_for_level(level);
        if (need<0 || xp<need) break;
    }
    return level-1;
}
long hd74_xp_add_bounded(long current, long delta)
{
    if (current < 0L) current=0L;
    if (current>HD74_XP_MAX) current=HD74_XP_MAX;
    if (delta<=0L) return current;
    if (delta>=HD74_XP_MAX-current) return HD74_XP_MAX;
    return current+delta;
}
