#ifndef HD79_MOUNT_WIRE_H
#define HD79_MOUNT_WIRE_H
#include "hd79_mount_roster.h"
#define HD79_MOUNT_MAX_STABLE_ROOM 0xffffffU
int hd79_mount_wire_encode(const hd79_mount_roster*,char[65],char[65]);
#endif
