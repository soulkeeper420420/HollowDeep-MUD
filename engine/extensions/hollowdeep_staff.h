/* Hollowdeep staff permissions. Include mstruct.h before this header. */
#ifndef HOLLOWDEEP_STAFF_H
#define HOLLOWDEEP_STAFF_H
#define HD_ROLE_PLAYER 0
#define HD_ROLE_MOD 1
#define HD_ROLE_ADMIN 2
#define HD_ROLE_OWNER 3
/* Persisted IDs are stable. Authority is ordered by hd_staff_rank(), not ID. */
#define HD_ROLE_IMPLEMENTOR 4
#define HD_ROLE_COUNT 5
int hd_staff_rank(int role);
int hstaff(creature *player, cmd *command);
int staffclan(creature *player, cmd *command);
const char *hd_staff_role_badge(int role);
const char *hd_staff_badge(creature *player);
int hmoderate(creature *player, cmd *command);
/* A negative role means storage could not be validated; callers must deny. */
int hd_staff_role(creature *player);
/* Record an authorized builder/DM attempt before changing the live world. */
int hd_staff_authorize_action(creature *player, int required, const char *action,
                              const char *target, const char *value);
int hd_staff_saved_name(const char *input, char *canonical);
/* Restricted sidecar access: -1 means absent, -2 means unsafe/unavailable. */
int hd_staff_open_data(const char *name);
int hd_staff_write_data(const char *name, const char *data, unsigned long size);
int hd_staff_can_chat(creature *player);
/* Called after native command resolution, before dispatch (covers aliases). */
int hd_staff_blocks_command(creature *player, int command_number);
#endif
