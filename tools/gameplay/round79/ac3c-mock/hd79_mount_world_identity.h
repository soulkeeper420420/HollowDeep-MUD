#ifndef HD79_AC3C_MOCK_WORLD_IDENTITY_H
#define HD79_AC3C_MOCK_WORLD_IDENTITY_H
#include "hd79_mount_presence_store.h"
struct creature;
int hd79_world_mount_bind(struct creature *owner,struct creature *mount,unsigned id,const hd79_mount_roster *r,const hd79_mount_presence *p);
int hd79_world_mount_present(struct creature *owner,unsigned id,const hd79_mount_roster *r,const hd79_mount_presence *p);
void hd79_world_mount_unbind_creature(const struct creature *mount);
#endif
