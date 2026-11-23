/* Local-only ABI-shaped stub; Linode compiles actual committed roster. */
#ifndef HD79_MOUNT_ROSTER_H
#define HD79_MOUNT_ROSTER_H
#include <stdint.h>
#define HD79_MOUNT_MAX_OWNED 6U
#define HD79_MOUNT_EPOCH_CHARS 24U
#define HD_MOUNT_HORSE 1
#define HD_MOUNT_GRIFFIN 5
typedef struct hd79_owned_mount {
 unsigned id; int species; unsigned endurance, stabled,stable_room;
} hd79_owned_mount;
typedef struct hd79_mount_roster {
 char epoch[HD79_MOUNT_EPOCH_CHARS+1U];
 uint32_t revision;
 unsigned count,active_id;
 hd79_owned_mount entries[HD79_MOUNT_MAX_OWNED];
} hd79_mount_roster;
int hd79_mount_roster_valid(const hd79_mount_roster *);
int hd79_mount_roster_new(hd79_mount_roster *,const char *);
int hd79_mount_board(const hd79_mount_roster *,hd79_mount_roster *,const char *,unsigned,int);
int hd79_mount_dismount(const hd79_mount_roster *,hd79_mount_roster *,const char *);
int hd79_mount_stable(const hd79_mount_roster *,hd79_mount_roster *,const char *,unsigned,unsigned,int,int);
int hd79_mount_retrieve(const hd79_mount_roster *,hd79_mount_roster *,const char *,unsigned,unsigned,int);
#endif
