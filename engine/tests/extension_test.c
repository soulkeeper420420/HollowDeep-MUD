/* Integration harness: compile the real extension against original engine types. */
#include "mstruct.h"
#include "hollowdeep.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>

static char output[16000];
static int checks;
/* Original Mordor global.c table: link the extension against the native values. */
long needed_exp[MAXALVL] = {
    512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 100000,
    166410, 277360, 394171, 560992, 757125, 1087504, 1402815,
    1739616, 2203457, 2799000, 3505139, 4465120, 5792661, 7319072,
    8874375, 15000000
};
void print(int fd, const char *format, ...)
{
    va_list args;
    size_t used = strlen(output);
    (void)fd;
    va_start(args, format);
    vsnprintf(output + used, sizeof(output) - used, format, args);
    va_end(args);
}
static void contains(const char *text)
{
    if (!strstr(output, text)) { fprintf(stderr, "Expected %s in:\n%s\n", text, output); exit(1); }
    checks++;
}
static void excludes(const char *text)
{
    if (strstr(output, text)) { fprintf(stderr, "Unexpected %s in:\n%s\n", text, output); exit(1); }
    checks++;
}
static void invoke(creature *player, const char *words, int (*handler)(creature *, cmd *))
{
    cmd command;
    creature original = *player;
    room location;
    int has_room = player->parent_rom != NULL;
    char copy[256], *part;
    if (has_room) location = *player->parent_rom;
    memset(&command, 0, sizeof(command));
    snprintf(copy, sizeof(copy), "%s", words);
    part = strtok(copy, " ");
    while (part && command.num < COMMANDMAX) {
        snprintf(command.str[command.num++], sizeof(command.str[0]), "%s", part);
        part = strtok(NULL, " ");
    }
    output[0] = '\0';
    handler(player, &command);
    assert(!memcmp(player, &original, sizeof(original)));
    if (has_room) assert(!memcmp(player->parent_rom, &location, sizeof(location)));
}
static void quest(creature *player, const char *words)
{
    invoke(player, words, hquest);
}
static void training_room(room *location, unsigned int class_number)
{
    unsigned int i;
    for (i = 0; i < 4; i++) {
        F_CLR(location, RTRAIN + 3 - i);
        if (class_number & (1U << i)) F_SET(location, RTRAIN + 3 - i);
    }
}
static void player_views(creature *player, room *location)
{
    creature original = *player;
    room original_room = *location;
    unsigned int i;
    player->parent_rom = location;
    player->class = FIGHTER; player->level = 1;
    player->hpcur = 7; player->hpmax = 22;
    player->mpcur = 2; player->mpmax = 5;
    player->experience = 123; player->gold = 100;
    F_SET(player, PSECOK);
    training_room(location, FIGHTER);

    invoke(player, "hprofile status", hprofile);
    contains("STATUS - Tester | Level 1 | Fighter");
    contains("HP 7/22 | MP 2/5"); contains("XP 123 | Gold 100");
    contains("Chronicle: 10/128 places | 4/4 badges");
    invoke(player, "hprofile unknown", hprofile); contains("Usage:");

    invoke(player, "hclass progress", hclass);
    contains("XP: 123 / 512 required; 389 more needed.");
    contains("Gold: 100 / 256 cost; 156 more needed.");
    contains("Training room: matches your class"); excludes("Ready:");
    player->experience = 512; player->gold = 256;
    for (i = 1; i <= 10; i++) {
        player->class = i; training_room(location, i);
        invoke(player, "hclass progress", hclass); contains("Ready: use train here");
    }
    player->class = FIGHTER; training_room(location, FIGHTER);
    player->gold = 255;
    invoke(player, "hclass progress", hclass); contains("1 more needed."); excludes("Ready:");
    player->gold = 256; player->experience = 511;
    invoke(player, "hclass progress", hclass); contains("XP: 511 / 512 required; 1 more needed."); excludes("Ready:");
    player->experience = 512;
    training_room(location, MAGE);
    invoke(player, "hclass progress", hclass); contains("find your class's training room"); excludes("Ready:");
    player->parent_rom = NULL;
    invoke(player, "hclass progress", hclass); contains("find your class's training room"); excludes("Ready:");
    player->parent_rom = location; training_room(location, FIGHTER);
    F_SET(player, PBLIND);
    invoke(player, "hclass progress", hclass); contains("blocked while you are blind"); excludes("Ready:");
    F_CLR(player, PBLIND); F_CLR(player, PSECOK);
    invoke(player, "hclass progress", hclass); contains("approval is pending"); excludes("Ready:");
    F_SET(player, PSECOK);

    player->level = 24;
    invoke(player, "hclass progress", hclass); contains("8874375 required"); contains("4437187 cost");
    player->level = 25;
    invoke(player, "hclass progress", hclass); contains("375000000 required"); contains("187500000 cost");
    player->level = 127;
    invoke(player, "hclass progress", hclass); contains("1905000000 required");
    player->level = (char)255;
    invoke(player, "hclass progress", hclass); contains("supported range"); excludes("Ready:");
    player->level = 0;
    invoke(player, "hclass progress", hclass); contains("level 1 or above");
    player->level = 1; player->class = DM;
    invoke(player, "hclass progress", hclass); contains("playable classes");
    invoke(player, "hprofile status", hprofile); contains("Other class");
    player->class = (char)255;
    invoke(player, "hclass progress", hclass); contains("playable classes");
    player->class = FIGHTER; player->experience = -1;
    invoke(player, "hclass progress", hclass); contains("unavailable for these character values");
    player->experience = 512; player->gold = -1;
    invoke(player, "hclass progress", hclass); contains("unavailable for these character values");
    player->gold = 256; needed_exp[0] = -1;
    invoke(player, "hclass progress", hclass); contains("unavailable for these character values");
    needed_exp[0] = 512;

    invoke(player, "hcommands mobile", hcommands); contains("MOBILE COMMANDS"); contains("ne nw se sw u d"); contains("Score: sc");
    invoke(player, "hcommands social", hcommands); contains("SOCIAL COMMANDS"); contains("lose - stop following your leader"); contains("group - list the people following you");
    invoke(player, "hcommands unknown", hcommands); contains("Usage:");
    *player = original; *location = original_room;
}
int main(int argc, char **argv)
{
    creature player;
    room location;
    cmd command;
    FILE *file;
    int i;
    assert(argc == 2 && chdir(argv[1]) == 0);
    memset(&player, 0, sizeof(player)); memset(&location, 0, sizeof(location)); memset(&command, 0, sizeof(command));
    strcpy(player.name, "Tester"); player.level = 1; player.class = FIGHTER; player.fd = 1; player.parent_rom = &location;
    player.gold = 123; player.experience = 456;

    quest(&player, "hquest next"); contains("hquest accept first-steps");
    assert(access("hollowdeep-data/tester.journal", F_OK) != 0); checks++;
    quest(&player, "hquest survey"); contains("Accept a chronicle first");
    quest(&player, "hquest claim first-steps"); contains("Accept this chronicle");
    quest(&player, "hquest accept first-steps"); contains("Accepted:");
    quest(&player, "hquest next"); contains("Remaining: 3 places; 0 levels.");
    quest(&player, "hquest claim first-steps"); contains("Not complete");
    for (i = 1; i <= 3; i++) { location.rom_num = i; quest(&player, "hquest survey"); contains("Unique places:"); }
    quest(&player, "hquest survey"); contains("already in your chronicle");
    location.rom_num = 0; quest(&player, "hquest survey"); contains("cannot survey"); location.rom_num = 3;
    quest(&player, "hquest next"); contains("Ready to claim"); contains("hquest claim first-steps");
    quest(&player, "hquest claim first-steps"); contains("Wayfarer badge");
    quest(&player, "hquest claim first-steps"); contains("already earned");
    output[0] = '\0'; hprofile(&player, &command); contains("Badge: Wayfarer"); contains("Recorded places: 3");
    strcpy(player.name, "Second"); output[0] = '\0'; hprofile(&player, &command); contains("No badges yet"); contains("Recorded places: 0"); strcpy(player.name, "Tester");
    assert(player.gold == 123 && player.experience == 456); checks++;
    quest(&player, "hquest accept apprentice"); contains("Accepted:");
    quest(&player, "hquest next"); contains("Remaining: 0 places; 2 levels."); contains("hclass progress");
    quest(&player, "hquest claim apprentice"); contains("Not complete");
    player.level = 3;
    quest(&player, "hquest claim apprentice"); contains("Adept badge");
    quest(&player, "hquest accept mapmaker"); contains("Accepted:");
    for (i = 4; i <= 10; i++) { location.rom_num = i; quest(&player, "hquest survey"); contains("Unique places:"); }
    quest(&player, "hquest claim mapmaker"); contains("Pathfinder badge");
    quest(&player, "hquest accept veteran"); contains("Accepted:");
    quest(&player, "hquest claim veteran"); contains("Not complete");
    player.level = 5;
    quest(&player, "hquest claim veteran"); contains("Veteran badge");
    quest(&player, "hquest status"); contains("first-steps"); contains("[claimed]");
    quest(&player, "hquest next"); contains("All chronicles are complete");

    /* Restart-style access: a fresh creature uses the journal on disk. */
    memset(&player, 0, sizeof(player)); strcpy(player.name, "Tester"); player.level = 5; player.class = MAGE;
    quest(&player, "hquest claim veteran"); contains("already earned");
    quest(&player, "hquest accept missing"); contains("Choose a quest ID");
    quest(&player, "hquest survey"); contains("cannot survey");
    output[0] = '\0'; hclass(&player, &command); contains("Mage:"); contains("enough experience and gold");
    output[0] = '\0'; hcommands(&player, &command); contains("hquest"); contains("flee can drop");
    player_views(&player, &location);

    /* Bad journals are rejected, and symlinks are never followed. */
    file = fopen("hollowdeep-data/tester.journal", "w"); assert(file); fputs("HOLLOWDEEP 1 1 1 2\n1\n1\n", file); fclose(file);
    quest(&player, "hquest survey"); contains("could not be read or saved");
    file = fopen("hollowdeep-data/tester.journal", "r"); assert(file); { char buffer[80]; assert(fgets(buffer, sizeof(buffer), file)); assert(strstr(buffer, "1 1 1 2")); } fclose(file); checks++;
    assert(unlink("hollowdeep-data/tester.journal") == 0);
    file = fopen("outside", "w"); assert(file); fputs("unchanged", file); fclose(file);
    assert(symlink("../outside", "hollowdeep-data/tester.journal") == 0);
    quest(&player, "hquest accept first-steps"); contains("could not be read or saved");
    file = fopen("outside", "r"); assert(file); { char buffer[30]; assert(fgets(buffer, sizeof(buffer), file)); assert(!strcmp(buffer, "unchanged")); } fclose(file); checks++;
    strcpy(player.name, "../outside"); quest(&player, "hquest accept first-steps"); contains("could not be read or saved");
    memset(player.name, 'A', sizeof(player.name)); quest(&player, "hquest"); contains("could not be read or saved");
    printf("%d extension behavior checks passed.\n", checks);
    return 0;
}
