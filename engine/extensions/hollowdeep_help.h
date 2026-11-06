#ifndef HOLLOWDEEP_HELP_H
#define HOLLOWDEEP_HELP_H
/* Include mstruct.h first. Help and catalogs never execute listed commands. */
int help(creature *player, cmd *command);
int dmcommands(creature *player, cmd *command);
int skills(creature *player, cmd *command);
int hd_native_command_allowed(creature *player, int command_number);
#endif
