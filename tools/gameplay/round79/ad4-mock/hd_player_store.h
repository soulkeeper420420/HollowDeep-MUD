#ifndef HD79_AD4_MOCK_PLAYER_STORE_H
#define HD79_AD4_MOCK_PLAYER_STORE_H
#define PLAYER 0
#define MONSTER 1
#define HD79_MOUNT_MAX_OWNED 6U
#define HD79_MOUNT_EPOCH_CHARS 24U
#define HD_MOUNT_HORSE 1
#define HD_MOUNT_DARK_DRAGON 6
#include <stdint.h>
typedef struct creature {
 char name[80]; char type,level; short hpcur,hpmax,rom_num;
} creature;
typedef struct hd79_owned_mount {
 unsigned id; int species;unsigned endurance,stabled,stable_room;
} hd79_owned_mount;
typedef struct hd79_mount_roster {
 char epoch[25]; uint32_t revision;unsigned count,active_id;
 hd79_owned_mount entries[HD79_MOUNT_MAX_OWNED];
} hd79_mount_roster;
typedef struct hd79_mount_presence {
 uint32_t revision;unsigned count,active_id,room[HD79_MOUNT_MAX_OWNED];
} hd79_mount_presence;
typedef struct hd79_ad_death_receipt {
 char epoch[25]; uint32_t serial;unsigned count,dead_mask;
} hd79_ad_death_receipt;
#endif
