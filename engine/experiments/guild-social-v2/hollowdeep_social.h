/* HollowDeep staged guild and charter integration. Include mstruct.h first. */
#ifndef HOLLOWDEEP_SOCIAL_H
#define HOLLOWDEEP_SOCIAL_H
int hd_global_chat(creature *player, cmd *command);
int hd_player_clan(creature *player, cmd *command);
int hd_clan_chat(creature *player, cmd *command);
int hd_staff_hub(creature *player, cmd *command);
int hd_guild_mint_deed(object *item);
int hd_guild_can_enter(creature *player, int room_number);
#endif
