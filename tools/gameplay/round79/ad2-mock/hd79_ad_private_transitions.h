#ifndef HD79_AD2_MOCK_TRANSITIONS_H
#define HD79_AD2_MOCK_TRANSITIONS_H
#include "hd79_mount_presence.h"
int hd79_ad_private_plan_action(const hd79_mount_roster *,
  const hd79_mount_presence *,unsigned,unsigned,unsigned,int,int,
  hd79_mount_roster *,hd79_mount_presence *);
#endif
