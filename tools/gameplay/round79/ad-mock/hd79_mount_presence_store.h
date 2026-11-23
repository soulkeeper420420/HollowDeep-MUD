#ifndef HD79_AD_MOCK_PRESENCE_STORE_H
#define HD79_AD_MOCK_PRESENCE_STORE_H
#define HD79_MOUNT_MAX_OWNED 6U
#define HD_MOUNT_HORSE 1
#define HD_MOUNT_DARK_DRAGON 6
#define HD79_PRESENCE_MAX_ROOM 0xffffffU
#define HD79_PRESENCE_STORE_OK 0
#define HD79_PRESENCE_STORE_ABSENT 1
#define HD79_PRESENCE_STORE_FAILURE -1
#include "hd_player_store.h"
typedef struct hd79_owned_mount { unsigned id; int species; unsigned endurance,stabled,stable_room; } hd79_owned_mount;
typedef struct hd79_mount_roster {
 char epoch[25];unsigned revision,count,active_id;
 hd79_owned_mount entries[6];
} hd79_mount_roster;
typedef struct hd79_mount_presence {
 unsigned revision,count,active_id,room[6];
} hd79_mount_presence;
int hd79_presence_store_read(const char *,hd79_mount_roster *,hd79_mount_presence *);
int hd79_presence_valid(const hd79_mount_roster *,const hd79_mount_presence *);
#endif
