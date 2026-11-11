/* Offline builder for disposable native saves and room header offsets. */
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "mstruct.h"

extern int load_ply(char *, creature **);
extern int save_ply(char *, creature *);

int main(int argc, char **argv)
{
    creature *player = NULL;
    if (argc == 1) {
        printf("%zu %zu\n", offsetof(room, trap), offsetof(room, trapexit));
        return 0;
    }
    if (argc != 3 || strncmp(argv[1], "Hd", 2) || load_ply(argv[1], &player) < 0)
        return 1;
    if (!strcmp(argv[2], "staff"))
        player->class = CARETAKER;
    else if (!strcmp(argv[2], "spell")) {
        player->class = MAGE;
        player->level = 35;
        player->intelligence = 18;
        player->dexterity = 1;
        player->mpmax = player->mpcur = 300;
        player->hpmax = player->hpcur = 300;
        S_SET(player, STELEP);
    } else
        return 2;
    player->rom_num = 1;
    return save_ply(argv[1], player) < 0;
}
