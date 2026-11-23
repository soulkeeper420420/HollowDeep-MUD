#ifndef HD79_MOUNT_PRESENCE_H
#define HD79_MOUNT_PRESENCE_H
#include "hd79_mount_roster.h"
#define HD79_PRESENCE_MAX_ROOM 0xffffffU
#define HD79_PRESENCE_DISMOUNT 2U
typedef struct hd79_mount_presence {uint32_t revision;unsigned count;unsigned active_id;unsigned room[6];} hd79_mount_presence;
int hd79_presence_valid(const hd79_mount_roster*,const hd79_mount_presence*);
int hd79_presence_encode(const hd79_mount_roster*,const hd79_mount_presence*,char[65]);
int hd79_presence_step(const hd79_mount_roster*,const hd79_mount_presence*,const hd79_mount_roster*,unsigned,unsigned,unsigned,int,int,hd79_mount_presence*);
#endif
