/*
 * HollowDeep Round 11U PRIVATE-ROOTFS ONLY rollback helper.
 *
 * Link using the candidate's 32-bit native object files (with main renamed
 * as in Round11Q fixture). Execute ONLY inside a disposable chroot with
 * rootfs/player containing disposable names. NO live-player input.
 *
 * CLI: /bin/round11u-relocate Hd<test> TOWN_SQUARE_ROOM_ID
 * Exit 0 = relocated a guild-district occupant; 3 = already elsewhere.
 * This is a test-only helper, not part of the MUD release build.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "mstruct.h"

extern int load_ply(char *, creature **);
extern int save_ply(char *, creature *);
extern int load_rom(int, room **);

int main(int argc, char **argv)
{
    creature *player = NULL;
    room *destination = NULL;
    char *end = NULL;
    long room_id;
    int i;
    /* Defense in depth: fail closed if copied to a non-test runtime. */
    if (!getenv("ROUND11U_DISPOSABLE_RELOCATION") ||
        strcmp(getenv("ROUND11U_DISPOSABLE_RELOCATION"), "PRIVATE_ONLY") ||
        access("/hollowdeep-data/round11u-private-sentinel", R_OK) != 0) {
        fprintf(stderr, "STOP: disposable-only relocation guard missing\n");
        return 2;
    }
    if (argc != 3) {
        fprintf(stderr, "Usage: round11u-relocate HdTESTNAME TOWN_ROOM\n");
        return 2;
    }
    if (strlen(argv[1]) < 5 || strlen(argv[1]) > 19 ||
        strncmp(argv[1], "Hd", 2)) {
        fprintf(stderr, "STOP: only disposable Hd test names are allowed\n");
        return 2;
    }
    for (i = 2; argv[1][i]; i++)
        if ((argv[1][i] < 'a' || argv[1][i] > 'z') &&
            (argv[1][i] < '0' || argv[1][i] > '9')) {
            fprintf(stderr, "STOP: unsupported disposable test name\n");
            return 2;
        }
    room_id = strtol(argv[2], &end, 10);
    if (!end || *end || room_id <= 0 || room_id >= 6000) {
        fprintf(stderr, "STOP: destination must be pre-existing non-guild room\n");
        return 2;
    }
    if (load_rom((int)room_id, &destination) < 0 || !destination) {
        fprintf(stderr, "STOP: destination room missing in private world\n");
        return 2;
    }
    if (load_ply(argv[1], &player) < 0 || !player) {
        fprintf(stderr, "STOP: disposable native player save unavailable\n");
        return 2;
    }
    if (player->rom_num < 6000 || player->rom_num > 6011) {
        printf("UNCHANGED: disposable character is outside the district\n");
        return 3;
    }
    player->rom_num = (short)room_id;
    /* Native load_ply cleared ready[]: carried equipment stays in inventory. */
    if (save_ply(argv[1], player) < 0) {
        fprintf(stderr, "STOP: unable to atomically save relocated player\n");
        return 4;
    }
    printf("RELOCATED: disposable character to verified predecessor room %ld\n",
           room_id);
    return 0;
}
