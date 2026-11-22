#ifndef HD79_MOUNT_STORE_MOCK_H
#define HD79_MOUNT_STORE_MOCK_H
#define HD79_MOUNT_STORE_OK 0
#define HD79_MOUNT_STORE_ABSENT 1
#define HD79_MOUNT_MAX_STABLE_ROOM 0xffffffU
#define HD79_MOUNT_MAX_OWNED 6U
typedef struct hd79_owned_mount {
 unsigned id;int species;unsigned endurance,stabled,stable_room;
} hd79_owned_mount;
typedef struct hd79_mount_roster {
 char epoch[25];unsigned revision,count,active_id;
 hd79_owned_mount entries[HD79_MOUNT_MAX_OWNED];
} hd79_mount_roster;
int hd79_mount_store_read(const char *name, hd79_mount_roster *out);
#endif
