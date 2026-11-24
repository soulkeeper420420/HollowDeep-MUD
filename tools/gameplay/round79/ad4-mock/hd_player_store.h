#ifndef HD79_AD4_MOCK_PLAYER_STORE_H
#define HD79_AD4_MOCK_PLAYER_STORE_H
#define PLAYER 0
#define MONSTER 1
#include "../hd79_mount_presence.h"
#include "../hd79_ad_death_receipt.h"
typedef struct creature {
 char name[80]; char type,level; short hpcur,hpmax,rom_num;
} creature;
#endif
