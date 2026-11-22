#ifndef MEXTERN_MOCK_Z_H
#define MEXTERN_MOCK_Z_H
#include "hd_player_store.h"
typedef struct cmd {int num;char fullstr[256];char str[8][80];long val[8];} cmd;
void print(int fd,const char *message);
#endif
