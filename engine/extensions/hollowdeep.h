/* Hollowdeep additions to original Mordor 3.00.
 * Include mstruct.h before this file. No saved Mordor structure is changed.
 */
#ifndef HOLLOWDEEP_EXTENSION_H
#define HOLLOWDEEP_EXTENSION_H
int hcommands(creature *player, cmd *command);
int hclass(creature *player, cmd *command);
int hquest(creature *player, cmd *command);
int hprofile(creature *player, cmd *command);
int spells(creature *player, cmd *command);
#endif
