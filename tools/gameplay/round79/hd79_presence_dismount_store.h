/* Round79AC1: native receipt-82 dismount transaction adapter. */
#ifndef HD79_PRESENCE_DISMOUNT_STORE_H
#define HD79_PRESENCE_DISMOUNT_STORE_H
#include "hd79_mount_presence_store.h"
#define HD79_DISMOUNT_SUCCESS 0
#define HD79_DISMOUNT_FAILURE (-1)
#define HD79_DISMOUNT_ABSENT 1
#define HD79_DISMOUNT_CONFLICT 2
#define HD79_DISMOUNT_UNCERTAIN 3
#define HD79_DISMOUNT_ON_FOOT 4
int hd79_presence_dismount_store(const char *name,unsigned room,
                                  hd79_mount_roster *out);
#endif
