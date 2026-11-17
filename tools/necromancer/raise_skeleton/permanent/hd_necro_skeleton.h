#ifndef HD_NECRO_SKELETON_H
#define HD_NECRO_SKELETON_H
/* Private Necromancer pet: stable native ABI, no mstruct.h inclusion. */
struct creature;
struct room;
struct cmd;
int hd_necro_raise(struct creature *owner, struct cmd *cmnd);
int hd_necro_raise_or_action(struct creature *owner, struct cmd *cmnd);
void hd_necro_skeleton_record_kill(struct creature *victim, struct creature *killer);
int hd_necro_skeleton_is_pet(struct creature *who);
int hd_necro_skeleton_can_heal(struct creature *healer);
void hd_necro_skeleton_assist(struct creature *owner, struct creature *target);
void hd_necro_skeleton_follow(struct creature *owner, struct room *old_room, struct room *new_room);
void hd_necro_skeleton_tick(long now);
void hd_necro_skeleton_logout(struct creature *owner);
void hd_necro_skeleton_reconnect(struct creature *owner);
void hd_necro_skeleton_on_free(struct creature *who);
struct creature *hd_necro_skeleton_probe(struct creature *owner);
#endif
