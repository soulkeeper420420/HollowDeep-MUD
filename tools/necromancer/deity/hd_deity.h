#ifndef HD_DEITY_H
#define HD_DEITY_H
/* Private playtest deity membership. Include mstruct.h first. */
#define HD_DEITY_MAX_ID 16
/* -1 = invalid/unavailable storage; 0 = unassigned; 1-16 = assigned. */
int hd_deity_get(const char *saved_name);
int hd_deity_assigned(const char *saved_name);
/* DM-only command, protected by both native class and audited staff role. */
int hd_dm_deity(creature *player, cmd *command);
#endif
