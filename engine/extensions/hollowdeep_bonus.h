#ifndef HOLLOWDEEP_BONUS_H
#define HOLLOWDEEP_BONUS_H
int hbonus(creature *player, cmd *command);
long hd_bonus_xp(creature *player, long base);
long hd_bonus_gold(long base);
int hd_bonus_can_take_gold(creature *player, object *item);
#endif
