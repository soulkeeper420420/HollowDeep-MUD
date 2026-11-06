/* Original Mordor types must be included before this header. */
#ifndef HOLLOWDEEP_STANCE_H
#define HOLLOWDEEP_STANCE_H
int hstance(creature *player, cmd *command);
int hd_stance_threshold(creature *attacker, creature *defender, int threshold);
#endif
