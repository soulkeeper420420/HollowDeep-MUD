#ifndef HD79_MOUNT_STORE_H
#define HD79_MOUNT_STORE_H
#include "hd79_mount_roster.h"
#define HD79_MOUNT_STORE_OK 0
#define HD79_MOUNT_STORE_ABSENT 1
int hd79_mount_store_read(const char*,hd79_mount_roster*);
#endif
