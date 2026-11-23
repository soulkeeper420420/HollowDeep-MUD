#ifndef HD79_AD2_MOCK_STORE_H
#define HD79_AD2_MOCK_STORE_H
#include "hd79_mount_presence.h"
#define HD79_PRESENCE_STORE_OK 0
#define HD79_PRESENCE_STORE_FAILURE (-1)
int hd79_presence_store_read(const char *,hd79_mount_roster *,hd79_mount_presence *);
#endif
