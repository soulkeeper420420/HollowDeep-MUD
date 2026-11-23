#ifndef HD79_AC3C_MOCK_ROSTER_H
#define HD79_AC3C_MOCK_ROSTER_H
#include <stdint.h>
#define HD79_MOUNT_MAX_OWNED 6U
#define HD79_MOUNT_EPOCH_CHARS 24U
#define HD_MOUNT_HORSE 1
#define HD_MOUNT_DARK_DRAGON 6
typedef struct hd79_owned_mount {
    unsigned id; int species; unsigned endurance,stabled,stable_room;
} hd79_owned_mount;
typedef struct hd79_mount_roster {
    char epoch[25];uint32_t revision; unsigned count,active_id;
    hd79_owned_mount entries[6];
} hd79_mount_roster;
int hd79_mount_roster_new(hd79_mount_roster *out,const char *epoch);
int hd79_mount_award(const hd79_mount_roster *previous,hd79_mount_roster *next,const char *epoch,int species,unsigned *id);
#endif
