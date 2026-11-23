#ifndef HD79_AC3C_MOCK_PLAYER_STORE_H
#define HD79_AC3C_MOCK_PLAYER_STORE_H
#include <stddef.h>
#define PLAYER 0
#define MONSTER 1
#define CMAX 3000
struct creature;
typedef struct crt_tag { struct crt_tag *next_tag; struct creature *crt; } ctag;
typedef struct room { short rom_num; ctag *first_mon; ctag *first_ply; } room;
typedef struct creature {
    char name[80];
    char type;
    short hpcur,hpmax;
    short rom_num;
    room *parent_rom;
    struct creature *following;
    ctag *first_fol;
    void *first_enm;
} creature;
#endif
