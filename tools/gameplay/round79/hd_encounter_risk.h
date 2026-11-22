/* Round 79A encounter scouting: deterministic, read-only danger labels. */
#ifndef HD_ENCOUNTER_RISK_H
#define HD_ENCOUNTER_RISK_H
enum hd_encounter_risk_rank {
    HD_ENCOUNTER_INVALID = -1,
    HD_ENCOUNTER_TRIVIAL = 0,
    HD_ENCOUNTER_MANAGEABLE = 1,
    HD_ENCOUNTER_DANGEROUS = 2,
    HD_ENCOUNTER_DEADLY = 3
};
/* Valid levels range 1..60. This module never reads or writes player saves. */
int hd_encounter_risk(int player_level, int monster_level);
const char *hd_encounter_risk_label(int rank);
#endif
