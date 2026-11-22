#ifndef HD79_MOUNT_STORE_H
#define HD79_MOUNT_STORE_H
#include "hd79_mount_roster.h"
#include "hd79_mount_wire.h"
enum { HD79_MOUNT_OK=0, HD79_MOUNT_ERROR=-1, HD79_MOUNT_CONFLICT=-2,
       HD79_MOUNT_UNCERTAIN=-3, HD79_MOUNT_ABSENT=1 };
int hd79_mount_read(const char *, hd79_mount_roster *);
int hd79_mount_change(creature *, const hd79_mount_roster *, unsigned, unsigned,
                      unsigned, int, const hd_travel_plan *, hd79_mount_roster *);
enum { HD79_MOUNT_BUY=1, HD79_MOUNT_BOARD, HD79_MOUNT_OFF,
       HD79_MOUNT_DEPOSIT, HD79_MOUNT_RETRIEVE, HD79_MOUNT_MOVE };
int hd79_mount_command(creature *, cmd *);
int hd79_mount_precommit(creature *, room *);
int hd79_mount_stable_room(int);
#endif
