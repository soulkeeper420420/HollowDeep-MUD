#ifndef HD79_AD_MOCK_PLAYER_STORE_H
#define HD79_AD_MOCK_PLAYER_STORE_H
#define PLAYER 0
#define MONSTER 1
struct creature;
typedef struct crt_tag { struct crt_tag *next_tag; struct creature *crt; } ctag;
typedef struct room { short rom_num; ctag *first_mon; ctag *first_ply; } room;
typedef struct creature {
 char name[80]; char type,level; short hpcur,hpmax,mpcur,mpmax,fd;
 short rom_num; room *parent_rom; unsigned long gold,experience;
 short ndice,sdice,pdice; unsigned char flags[8],spells[16];
} creature;
#endif
