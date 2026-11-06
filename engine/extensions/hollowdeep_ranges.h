#ifndef HOLLOWDEEP_RANGES_H
#define HOLLOWDEEP_RANGES_H
/* Positive=authorized, zero=outside assignment, negative=invalid storage. */
int hd_build_access(creature *player, int room_number);
/* Handle assign/unassign/ranges/mine, returning 1 when the action matched. */
int hd_build_ranges(creature *player, const char *action, const char *arguments);
#endif
