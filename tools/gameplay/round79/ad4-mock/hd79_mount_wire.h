#ifndef HD79_AD4_MOCK_WIRE_H
#define HD79_AD4_MOCK_WIRE_H
#include "hd_player_store.h"
int hd79_mount_wire_encode(const hd79_mount_roster *,char [65],char [65]);
int hd79_presence_encode(const hd79_mount_roster *,const hd79_mount_presence *,char [65]);
int hd79_ad_death_wire_encode(const hd79_mount_roster *,const hd79_ad_death_receipt *,char [65]);
int hd79_presence_valid(const hd79_mount_roster *,const hd79_mount_presence *);
int hd79_ad_death_valid(const hd79_mount_roster *,const hd79_ad_death_receipt *);
int hd79_ad_death_mark(const hd79_mount_roster *,const hd79_ad_death_receipt *,unsigned,hd79_ad_death_receipt *);
#endif
