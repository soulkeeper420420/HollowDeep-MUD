/* Exercise actual staff permissions/persistence against native Mordor types. */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static char output[32000];
static int checks, disconnected = -1, broadcasts;
static long clock_now = 1800000000L;
static creature founder, admin, moderator, visitor, second_owner, long_name;
long hd_staff_test_now(void) { return clock_now; }
void print(int fd, const char *format, ...)
{
    va_list args;
    size_t used = strlen(output);
    (void)fd;
    va_start(args, format);
    vsnprintf(output + used, sizeof(output) - used, format, args);
    va_end(args);
}
void broadcast(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    vsnprintf(output, sizeof(output), format, args);
    va_end(args);
    broadcasts++;
}
void output_buf(void) {}
void disconnect(int fd) { disconnected = fd; }
creature *find_who(char *name)
{
    creature *players[] = {&founder, &admin, &moderator, &visitor, &second_owner, &long_name};
    unsigned int i;
    for (i = 0; i < sizeof(players)/sizeof(players[0]); i++)
        if (!strcmp(name, players[i]->name) && players[i]->fd >= 0) return players[i];
    return NULL;
}
static void check(int condition) { assert(condition); checks++; }
static void contains(const char *text)
{
    if (!strstr(output, text)) { fprintf(stderr, "Missing %s in: %s\n", text, output); exit(1); }
    checks++;
}
static void command(creature *player, const char *line, int moderation)
{
    cmd parsed;
    char copy[256], *word;
    memset(&parsed, 0, sizeof(parsed));
    snprintf(parsed.fullstr, sizeof(parsed.fullstr), "%s", line);
    snprintf(copy, sizeof(copy), "%s", line);
    word = strtok(copy, " ");
    while (word && parsed.num < COMMANDMAX) {
        snprintf(parsed.str[parsed.num++], sizeof(parsed.str[0]), "%s", word);
        word = strtok(NULL, " ");
    }
    output[0] = 0;
    if (moderation) hmoderate(player, &parsed); else hstaff(player, &parsed);
}
static void character(creature *player, const char *name, int fd, int class_id)
{
    char path[160];
    FILE *file;
    memset(player, 0, sizeof(*player));
    strcpy(player->name, name);
    player->type = PLAYER; player->fd = fd; player->class = class_id; player->level = 1;
    snprintf(path, sizeof(path), "%s/%s", PLAYERPATH, name);
    file = fopen(path, "w"); assert(file); fputs("saved character sentinel", file); assert(!fclose(file));
}
int main(int argc, char **argv)
{
    FILE *file;
    char saved[32768], actual[128];
    size_t saved_size;
    creature copy;
    int chat_commands[] = {4, 17, 25, 29, 53, 57, 59};
    unsigned int i;
    assert(argc == 2 && !chdir(argv[1]));
    assert(!mkdir(PLAYERPATH, 0700));
    character(&founder, DMNAME, 1, DM);
    character(&admin, "Adminhero", 2, FIGHTER);
    character(&moderator, "Modhero", 3, FIGHTER);
    character(&visitor, "Visitor", 4, MAGE);
    character(&second_owner, "Ownerhero", 5, FIGHTER);
    check(hd_staff_role(&founder) == HD_ROLE_OWNER);
    copy = founder; copy.class = FIGHTER; check(hd_staff_role(&copy) == -1);
    copy = founder; copy.type = MONSTER; check(hd_staff_role(&copy) == -1);
    check(hd_staff_role(&visitor) == HD_ROLE_PLAYER);
    /* Original Mordor accepts names through 19 letters, not password length. */
    character(&copy, "Abcdefghijklmno", 6, FIGHTER);
    check(hd_staff_can_chat(&copy));
    character(&long_name, "Abcdefghijklmnopqrs", 7, FIGHTER);
    check(hd_staff_can_chat(&long_name));
    command(&founder, "hstaff grant Abcdefghijklmnopqrs mod", 0); contains("now has the mod role");
    check(hd_staff_role(&long_name) == HD_ROLE_MOD);
    command(&long_name, "hmoderate announce A long named keeper", 1); contains("Abcdefghijklmnopqrs");
    command(&founder, "hstaff audit", 0); contains("Abcdefghijklmnopqrs announce");
    command(&founder, "hstaff revoke Abcdefghijklmnopqrs", 0); contains("now has the player role");
    command(&founder, "hmoderate mute Abcdefghijklmnopqrs 1", 1); contains("muted for 1");
    check(!hd_staff_can_chat(&long_name));
    command(&founder, "hmoderate unmute Abcdefghijklmnopqrs", 1); contains("may chat again");
    check(hd_staff_can_chat(&long_name));
    copy = long_name; strcpy(copy.name, "Abcdefghijklmnopqrst");
    check(hd_staff_role(&copy) == -1); /* Beyond the original login boundary. */
    broadcasts = 0;
    command(&visitor, "hstaff grant Visitor owner", 0); contains("permission required");
    command(&founder, "hstaff grant Adminhero admin", 0); contains("now has the admin role");
    check(hd_staff_role(&admin) == HD_ROLE_ADMIN);
    check(admin.class == FIGHTER && admin.level == 1);
    command(&admin, "hstaff grant Modhero mod", 0); contains("now has the mod role");
    command(&moderator, "hstaff grant Visitor mod", 0); contains("permission required");
    command(&admin, "hstaff grant Visitor owner", 0); contains("Only an owner");
    command(&admin, "hstaff grant Visitor admin", 0); contains("Only an owner");
    command(&founder, "hstaff grant Ownerhero owner", 0); contains("now has the owner role");
    command(&admin, "hstaff revoke Ownerhero", 0); contains("Only an owner");
    command(&second_owner, "hstaff revoke Realmkeeper", 0); contains("protected");
    command(&second_owner, "hstaff revoke Ownerhero", 0); contains("own role");
    command(&founder, "hstaff grant Nobody mod", 0); contains("existing saved character");
    command(&founder, "hstaff grant ../outside mod", 0); contains("existing saved character");
    copy = admin; check(hd_staff_role(&copy) == HD_ROLE_ADMIN);
    command(&visitor, "hstaff list", 0); contains("Staff permission");
    command(&moderator, "hstaff list", 0); contains("Adminhero: admin");
    command(&moderator, "hstaff audit", 0); contains("Admin permission");
    command(&moderator, "hmoderate mute Adminhero", 1); contains("below your own");
    command(&moderator, "hmoderate mute Visitor 0", 1); contains("1-1440");
    command(&moderator, "hmoderate mute Visitor 1441", 1); contains("1-1440");
    {
        cmd native;
        memset(&native, 0, sizeof(native));
        strcpy(native.fullstr, "hmoderate mute Visitor 1");
        strcpy(native.str[0], "hmoderate"); strcpy(native.str[1], "mute"); strcpy(native.str[2], "visitor");
        native.num = 3; native.val[2] = 1; /* Actual legacy numeric-selector parse. */
        output[0] = 0; hmoderate(&moderator, &native); contains("muted for 1");
    }
    command(&moderator, "hmoderate mute Visitor 1", 1); contains("muted for 1");
    for (i = 0; i < sizeof(chat_commands)/sizeof(chat_commands[0]); i++)
        check(hd_staff_blocks_command(&visitor, chat_commands[i]));
    check(!hd_staff_blocks_command(&visitor, 52));
    check(!hd_staff_blocks_command(&visitor, 1));
    clock_now += 61; check(hd_staff_can_chat(&visitor));
    command(&moderator, "hmoderate mute Visitor", 1); contains("muted for 10");
    command(&moderator, "hmoderate unmute Visitor", 1); contains("may chat again");
    check(hd_staff_can_chat(&visitor));
    command(&admin, "hmoderate mute Modhero 1", 1); contains("muted for 1");
    command(&moderator, "hmoderate announce Cannot speak", 1); contains("You are muted");
    check(broadcasts == 0);
    command(&admin, "hmoderate unmute Modhero", 1); contains("may chat again");
    command(&moderator, "hmoderate announce Welcome adventurers!", 1); contains("Welcome adventurers!");
    check(broadcasts == 1);
    command(&moderator, "hmoderate announce bad\033[31m", 1); contains("printable ASCII");
    check(broadcasts == 1);
    command(&moderator, "hmoderate kick Visitor", 1); contains("normal save/logout");
    check(disconnected == visitor.fd);
    disconnected = -1;
    command(&moderator, "hmoderate kick Adminhero", 1); contains("below your own"); check(disconnected == -1);
    visitor.class = CARETAKER;
    command(&moderator, "hmoderate kick Visitor", 1); contains("Only an owner"); check(disconnected == -1);
    visitor.class = MAGE;
    command(&founder, "hstaff revoke Adminhero", 0); contains("now has the player role");
    check(hd_staff_role(&admin) == HD_ROLE_PLAYER);
    command(&founder, "hstaff audit", 0); contains("RECENT STAFF ACTIONS");
    file = fopen("hollowdeep-data/staff.db", "r"); assert(file);
    saved_size = fread(saved, 1, sizeof(saved)-1, file); saved[saved_size] = 0; fclose(file);
    check(!strstr(saved, "Welcome adventurers!"));
    file = fopen("hollowdeep-data/staff.db", "w"); assert(file); fputs("corrupted", file); fclose(file);
    check(hd_staff_role(&founder) == -1);
    command(&founder, "hstaff grant Visitor owner", 0); contains("unavailable");
    check(!hd_staff_can_chat(&visitor));
    check(!hd_staff_blocks_command(&visitor, 52));
    file = fopen("hollowdeep-data/staff.db", "r"); assert(file); assert(fgets(actual, sizeof(actual), file)); fclose(file);
    check(!strcmp(actual, "corrupted"));
    assert(!unlink("hollowdeep-data/staff.db"));
    file = fopen("outside", "w"); assert(file); fputs("keep", file); fclose(file);
    assert(!symlink("../outside", "hollowdeep-data/staff.db")); check(hd_staff_role(&founder) == -1);
    assert(!unlink("hollowdeep-data/staff.db"));
    assert(!mkfifo("hollowdeep-data/staff.db", 0600)); check(hd_staff_role(&founder) == -1);
    assert(!unlink("hollowdeep-data/staff.db"));
    file = fopen("hollowdeep-data/staff.db", "w"); assert(file); assert(fwrite(saved, 1, saved_size, file) == saved_size); fclose(file);
    assert(!symlink("../outside", PLAYERPATH "/Linked"));
    command(&founder, "hstaff grant Linked admin", 0); contains("existing saved character");
    check(hd_staff_role(&second_owner) == HD_ROLE_OWNER);
    file = fopen(PLAYERPATH "/Visitor", "r"); assert(file); assert(fgets(actual, sizeof(actual), file)); fclose(file);
    check(!strcmp(actual, "saved character sentinel"));
    printf("%d staff permission and persistence checks passed.\n", checks);
    return 0;
}
