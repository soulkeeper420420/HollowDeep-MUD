#ifndef HD79_AC2_MOCK_PLAYER_STORE_H
#define HD79_AC2_MOCK_PLAYER_STORE_H
/* Deliberately provide native types here, NOT from mextern.h.
 * The accepted ELF32 game follows the same hd_player_store.h include order. */
#include "mextern.h"
#define PLAYER 0
#define MONSTER 1
struct creature;
typedef struct crt_tag {
    struct crt_tag *next_tag;
    struct creature *crt;
} ctag;
typedef struct room {
    short rom_num;
    ctag *first_mon;
    ctag *first_ply;
} room;
typedef struct creature {
    char name[80];
    char type;
    short hpcur,hpmax;
    short rom_num;
    room *parent_rom;
} creature;
#endif
