/* Round 79A: level-relative estimates, not exact monster stats. */
#include "hd_encounter_risk.h"

int hd_encounter_risk(int player_level, int monster_level)
{
    int delta;
    if (player_level < 1 || player_level > 60 ||
        monster_level < 1 || monster_level > 60)
        return HD_ENCOUNTER_INVALID;
    delta = monster_level - player_level;
    if (delta <= -5) return HD_ENCOUNTER_TRIVIAL;
    if (delta <= -1) return HD_ENCOUNTER_MANAGEABLE;
    if (delta <= 3) return HD_ENCOUNTER_DANGEROUS;
    return HD_ENCOUNTER_DEADLY;
}
const char *hd_encounter_risk_label(int rank)
{
    switch (rank) {
    case HD_ENCOUNTER_TRIVIAL: return "trivial";
    case HD_ENCOUNTER_MANAGEABLE: return "manageable";
    case HD_ENCOUNTER_DANGEROUS: return "dangerous";
    case HD_ENCOUNTER_DEADLY: return "deadly";
    default: return "unknown";
    }
}
