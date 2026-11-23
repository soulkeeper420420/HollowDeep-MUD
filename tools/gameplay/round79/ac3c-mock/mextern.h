#ifndef HD79_AC3C_MOCK_MEXTERN_H
#define HD79_AC3C_MOCK_MEXTERN_H
#include "hd_player_store.h"
int load_crt(int id, creature **crt);
void add_crt_rom(creature *crt,room *r,int count);
void del_crt_rom(creature *crt,room *r);
void free_crt(creature *crt);
#endif
