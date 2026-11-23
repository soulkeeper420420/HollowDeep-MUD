#ifndef HD79_AD_MOCK_WORLD_IDENTITY_H
#define HD79_AD_MOCK_WORLD_IDENTITY_H
#include "hd79_mount_presence_store.h"
int hd79_world_mount_bind(creature *,creature *,unsigned,const hd79_mount_roster *,const hd79_mount_presence *);
int hd79_world_mount_present(creature *,unsigned,const hd79_mount_roster *,const hd79_mount_presence *);
void hd79_world_mount_unbind_creature(const creature *);
#endif
