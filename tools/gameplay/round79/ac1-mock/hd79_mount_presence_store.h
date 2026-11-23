#ifndef HD79_MOUNT_PRESENCE_STORE_H
#define HD79_MOUNT_PRESENCE_STORE_H
#include "hd79_mount_presence.h"
#define HD79_PRESENCE_STORE_OK 0
#define HD79_PRESENCE_STORE_FAILURE (-1)
#define HD79_PRESENCE_STORE_ABSENT 1
#define HD79_PRESENCE_STORE_CONFLICT 2
#define HD79_PRESENCE_STORE_UNCERTAIN 3
int hd79_presence_store_read(const char*,hd79_mount_roster*,hd79_mount_presence*);
int hd79_presence_store_commit(const char*,const hd79_mount_roster*,const hd79_mount_presence*,const hd79_mount_roster*,const hd79_mount_presence*,hd79_mount_roster*,hd79_mount_presence*);
#endif
