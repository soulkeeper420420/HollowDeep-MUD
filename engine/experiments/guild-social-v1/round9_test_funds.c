/*
 * ROUND 9 ISOLATED SHOP TEST ONLY. NEVER COMPILE INTO PRODUCTION.
 * This command is compiled exclusively with -DHD_ROUND9_ISOLATED_FUNDS=1
 * and must execute only in a disposable, network-isolated test rootfs.
 * It grants 3,000 gold once to a throwaway Hd* test player so the native
 * shop buy path can exercise a 2,500-gold Clan Deed.
 */
#include "mstruct.h"
#include <stdio.h>
#include <string.h>

#ifndef HD_ROUND9_ISOLATED_FUNDS
#error "This source must never compile outside an explicitly flagged isolated test"
#endif

extern void print(int fd, const char *format, ...);

int hd_round9_testfund(creature *player, cmd *command)
{
    (void)command;
    if (!player || player->fd < 0 || !player->parent_rom ||
        player->parent_rom->rom_num != 1 ||
        strncmp(player->name, "Hd", 2) != 0 ||
        strlen(player->name) < 5 || strlen(player->name) > 19) {
        if (player && player->fd >= 0)
            print(player->fd, "Round9 test grant not permitted.\n");
        return 0;
    }
    if (player->gold != 0) {
        print(player->fd, "Round9 test grant already used or gold not zero.\n");
        return 0;
    }
    player->gold = 3000L;
    print(player->fd, "Round9 isolated test gold granted: 3000.\n");
    return 0;
}
