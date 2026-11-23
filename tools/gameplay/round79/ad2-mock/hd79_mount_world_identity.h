#ifndef HD79_AD2_MOCK_WORLD_H
#define HD79_AD2_MOCK_WORLD_H
#include "hd79_mount_presence.h"
struct creature;
int hd79_world_mount_present(struct creature *,unsigned,
    const hd79_mount_roster *,const hd79_mount_presence *);
#endif
