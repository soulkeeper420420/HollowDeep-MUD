/* Hollowdeep staff permissions. Include mstruct.h before this header. */
#ifndef HOLLOWDEEP_STAFF_H
#define HOLLOWDEEP_STAFF_H
#define HD_ROLE_PLAYER 0
#define HD_ROLE_MOD 1
#define HD_ROLE_ADMIN 2
#define HD_ROLE_OWNER 3
int hstaff(creature *player, cmd *command);
int hmoderate(creature *player, cmd *command);
/* A negative role means storage could not be validated; callers must deny. */
int hd_staff_role(creature *player);
int hd_staff_can_chat(creature *player);
/* Called after native command resolution, before dispatch (covers aliases). */
int hd_staff_blocks_command(creature *player, int command_number);
#endif
