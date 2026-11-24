#ifndef HD79_AD4_MOCK_FOUR_H
#define HD79_AD4_MOCK_FOUR_H
#include "hd_player_store.h"
#define HD79_AD_FOUR_OK 0
#define HD79_AD_FOUR_FAILURE (-1)
#define HD79_AD_FOUR_ABSENT 1
#define HD79_AD_FOUR_CONFLICT 2
#define HD79_AD_FOUR_UNCERTAIN 3
int hd79_ad_four_store_read(const char *,hd79_mount_roster *,hd79_mount_presence *,hd79_ad_death_receipt *);
int hd79_ad_four_store_mark_dead(const char *,const hd79_mount_roster *,const hd79_mount_presence *,const hd79_ad_death_receipt *,unsigned,hd79_ad_death_receipt *);
#endif
