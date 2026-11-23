#ifndef MEXTERN_MOCK_H
#define MEXTERN_MOCK_H
#include "hd_player_store.h"
#define COMMANDMAX 10
#define MAX_TOKEN_SIZE 80
typedef struct cmd {
    int num;
    char fullstr[256];
    char str[COMMANDMAX][MAX_TOKEN_SIZE];
    long val[COMMANDMAX];
} cmd;
void print(int fd,const char *msg);
#endif
