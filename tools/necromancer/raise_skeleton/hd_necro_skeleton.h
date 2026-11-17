#ifndef HD_NECRO_SKELETON_H
#define HD_NECRO_SKELETON_H
/* Round 74 private Necromancer test skill. Avoid mstruct.h double inclusion. */
struct creature;
struct room;
struct cmd;
int hd_necro_raise(struct creature *owner, struct cmd *cmnd);
int hd_necro_raise_or_action(struct creature *owner, struct cmd *cmnd);
void hd_necro_skeleton_assist(struct creature *owner, struct creature *target);
void hd_necro_skeleton_follow(struct creature *owner, struct room *old_room, struct room *new_room);
void hd_necro_skeleton_tick(long now);
void hd_necro_skeleton_logout(struct creature *owner);
void hd_necro_skeleton_on_free(struct creature *who);
/* Pointer-only private test probe; must not be used to grant player rewards. */
struct creature *hd_necro_skeleton_probe(struct creature *owner);
#endif
