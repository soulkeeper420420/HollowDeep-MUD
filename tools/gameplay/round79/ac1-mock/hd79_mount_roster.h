#ifndef HD79_MOUNT_ROSTER_H
#define HD79_MOUNT_ROSTER_H
#include <stdint.h>
#define HD79_MOUNT_MAX_OWNED 6U
typedef struct hd79_owned_mount {unsigned id;int species;unsigned endurance;unsigned stabled;unsigned stable_room;} hd79_owned_mount;
typedef struct hd79_mount_roster {char epoch[25];uint32_t revision;unsigned count;unsigned active_id;hd79_owned_mount entries[6];} hd79_mount_roster;
int hd79_mount_dismount(const hd79_mount_roster*,hd79_mount_roster*,const char*);
#endif
