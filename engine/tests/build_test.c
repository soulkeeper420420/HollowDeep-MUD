/* Test actual permissions and file commits with an isolated native-world adapter. */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_build.h"
#include "hollowdeep_ranges.h"
#include "hollowdeep_bonus.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static creature founder, owner, admin, moderator, implementor, visitor;
static room first, second;
static char output[32768];
static int checks, writes, fail_write, moves;
static long clock_now = 1800000000L;
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
void broadcast(const char *format, ...) { (void)format; }
void output_buf(void) {}
void disconnect(int fd) { (void)fd; }
creature *find_who(char *name)
{
    creature *all[] = {&founder, &owner, &admin, &moderator, &implementor, &visitor};
    size_t i;
    for (i = 0; i < sizeof(all)/sizeof(all[0]); i++) if (!strcmp(name, all[i]->name)) return all[i];
    return NULL;
}
int load_rom(int id, room **result)
{
    if (id != 10 && id != 20) return -1;
    *result = id == 10 ? &first : &second;
    return 0;
}
int write_rom(int fd, room *location, int permanent_only)
{
    writes++;
    assert(permanent_only == PERMONLY);
    if (fail_write) { assert(write(fd, "partial", 7) == 7); return -1; }
    assert(write(fd, location->name, sizeof(location->name)) == sizeof(location->name));
    return 0;
}
void del_ply_rom(creature *player, room *location) { assert(player->parent_rom == location); player->parent_rom = NULL; }
void add_ply_rom(creature *player, room *location) { player->parent_rom = location; player->rom_num = location->rom_num; moves++; }
static void check(int condition) { assert(condition); checks++; }
static void contains(const char *text)
{
    if (!strstr(output, text)) { fprintf(stderr, "Missing %s in %s\n", text, output); exit(1); }
    checks++;
}
static void call(creature *player, const char *line)
{
    cmd command;
    memset(&command, 0, sizeof(command));
    snprintf(command.fullstr, sizeof(command.fullstr), "%s", line);
    output[0] = 0;
    /* Deliberately omit the native tokens: handlers must parse literal text. */
    if (!strncmp(line, "hbuild", 6)) hbuild(player, &command);
    else if (!strncmp(line, "hbonus", 6)) hbonus(player, &command);
    else if (!strncmp(line, "hdm", 3)) hdm(player, &command);
    else if (!strncmp(line, "hmoderate", 9)) hmoderate(player, &command);
    else hstaff(player, &command);
}
static void character(creature *player, const char *name, int fd, int class_number)
{
    char path[256];
    FILE *file;
    strcpy(player->name, name); player->fd = fd; player->type = PLAYER;
    player->class = class_number; player->level = 1; player->parent_rom = &first; player->rom_num = 10;
    player->hpcur = 1; player->hpmax = 40; player->mpcur = 0; player->mpmax = 20;
    snprintf(path, sizeof(path), "%s/%s", PLAYERPATH, name);
    file = fopen(path, "w"); assert(file); fputs("saved character sentinel", file); fclose(file);
}
static void disk_name(const char *expected)
{
    char name[80] = {0};
    FILE *file = fopen(ROOMPATH "/r00010", "r"); assert(file);
    assert(fread(name, 1, sizeof(name), file) > 0); fclose(file);
    check(!strcmp(name, expected));
}
int main(int argc, char **argv)
{
    FILE *file;
    char saved[32768], overlong[256];
    size_t saved_size;
    int previous_writes;
    creature before;
    etag combat;
    object money;
    creature monster;
    ctag monster_tag;
    (void)argc;
    assert(chdir(argv[1]) == 0);
    assert(mkdir(ROOMPATH, 0700) == 0); assert(mkdir(PLAYERPATH, 0700) == 0);
    first.rom_num = 10; strcpy(first.name, "Original room"); second.rom_num = 20;
    file = fopen(ROOMPATH "/r00010", "w"); assert(file); fputs(first.name, file); fclose(file);
    character(&founder, DMNAME, 1, DM); character(&owner, "Ownerhero", 2, FIGHTER);
    character(&admin, "Adminhero", 3, MAGE); character(&moderator, "Modhero", 4, FIGHTER);
    character(&visitor, "Visitor", 5, MAGE);
    character(&implementor, "Implhero", 6, MAGE);
    call(&founder, "hstaff grant Ownerhero owner"); contains("now has the owner");
    call(&founder, "hstaff grant Adminhero admin"); contains("now has the admin");
    call(&admin, "hstaff grant Modhero mod"); contains("now has the mod");
    call(&admin, "hstaff grant Implhero implementor"); contains("now has the implementor role");
    check(hd_staff_role(&implementor) == HD_ROLE_IMPLEMENTOR);
    check(HD_ROLE_MOD == 1 && HD_ROLE_ADMIN == 2 && HD_ROLE_OWNER == 3);
    check(hd_staff_rank(HD_ROLE_IMPLEMENTOR) == hd_staff_rank(HD_ROLE_MOD));
    check(hd_staff_rank(-1) == -1 && hd_staff_rank(HD_ROLE_COUNT) == -1);
    call(&implementor, "hstaff whoami"); contains("role: implementor");
    call(&implementor, "hstaff list"); contains("Implhero: implementor");
    call(&implementor, "hstaff audit"); contains("Admin permission");
    call(&implementor, "hstaff grant Visitor mod"); contains("permission required");
    call(&implementor, "hmoderate mute Modhero 1"); contains("below your own");
    call(&moderator, "hmoderate mute Implhero 1"); contains("below your own");
    call(&implementor, "hmoderate mute Adminhero 1"); contains("below your own");
    call(&implementor, "hmoderate mute Ownerhero 1"); contains("below your own");
    call(&implementor, "hmoderate mute Visitor 1"); contains("muted for 1");
    call(&implementor, "hmoderate unmute Visitor"); contains("may chat again");
    call(&admin, "hmoderate mute Implhero 1"); contains("muted for 1");
    call(&admin, "hmoderate unmute Implhero"); contains("may chat again");
    call(&implementor, "hdm restore"); contains("Admin permission");
    call(&implementor, "hdm goto 20"); contains("Admin permission");
    call(&implementor, "hbuild assign Visitor 8000"); contains("Owner permission");
    call(&implementor, "hbuild name Not assigned"); contains("assigned room range");
    call(&implementor, "hbuild info"); contains("Room 10: Original room");
    check(implementor.class == MAGE && implementor.level == 1 && moves == 0 && writes == 0);
    call(&admin, "hbuild name Needs allocation"); contains("assigned room range");
    call(&founder, "hbuild assign Adminhero 10 11"); contains("10-20 (11 rooms)");
    call(&founder, "hbuild assign Adminhero 8999 1"); contains("8999-8999");
    call(&admin, "hbuild assign Visitor 8000"); contains("Owner permission");
    call(&visitor, "hbuild info"); contains("Moderator permission");
    call(&moderator, "hbuild info"); contains("Room 10: Original room");
    call(&moderator, "hbuild create 8000"); contains("assigned room range"); check(writes == 0);
    call(&moderator, "hdm goto 20"); contains("Admin permission"); check(moves == 0);
    before = admin;
    call(&admin, "hbuild name The Hall of 42 Candles"); contains("name saved"); disk_name("The Hall of 42 Candles");
    check(!memcmp(&before, &admin, sizeof(admin)));
    call(&admin, "hbuild describe The road is long and full of wonders."); contains("describe saved");
    check(!strcmp(first.long_desc, "The road is long and full of wonders.\n"));
    fail_write = 1;
    call(&admin, "hbuild name Broken save"); contains("not applied");
    check(!strcmp(first.name, "The Hall of 42 Candles")); disk_name("The Hall of 42 Candles");
    call(&admin, "hbuild describe Failed description"); contains("not applied");
    check(!strcmp(first.long_desc, "The road is long and full of wonders.\n"));
    fail_write = 0;
    call(&admin, "hbuild create 8999"); contains("Created room 8999");
    call(&admin, "hbuild create 8999"); contains("already exists");
    previous_writes = writes;
    call(&admin, "hbuild create 9000"); contains("exact syntax");
    call(&admin, "hbuild create -1"); contains("exact syntax");
    call(&admin, "hbuild create 20 extra"); contains("exact syntax");
    call(&admin, "hbuild create ../../out"); contains("exact syntax"); check(writes == previous_writes);
    memset(overlong, 'a', sizeof(overlong)); strcpy(overlong, "hbuild name ");
    memset(overlong + 12, 'a', 80); overlong[92] = 0;
    call(&admin, overlong); contains("1-79");
    call(&admin, "hbuild name Bad\033[31m"); contains("printable"); check(writes == previous_writes);
    call(&admin, "hbuild link north 20"); contains("one-way");
    check(first.first_ext && first.first_ext->ext->room == 20 && !second.first_ext);
    call(&admin, "hbuild link north 10"); contains("already exists"); check(first.first_ext->ext->room == 20);
    fail_write = 1;
    call(&admin, "hbuild unlink north"); contains("unchanged"); check(first.first_ext != NULL);
    call(&admin, "hbuild link south 20"); contains("unchanged"); check(first.first_ext->next_tag == NULL);
    fail_write = 0;
    call(&admin, "hbuild unlink north"); contains("removed and saved"); check(first.first_ext == NULL);
    call(&admin, "hbuild link south 8998"); contains("destination must also");
    call(&admin, "hbuild link south 8999"); contains("does not exist");
    call(&founder, "hbuild assign Visitor 8000"); contains("8000-8049 (50 rooms)");
    call(&visitor, "hbuild mine"); contains("8000-8049 (50 rooms)");
    call(&founder, "hbuild assign Modhero 8049 50"); contains("overlaps Visitor");
    call(&founder, "hbuild assign Modhero 8050 50"); contains("8050-8099");
    call(&founder, "hbuild assign Visitor 8980 50"); contains("count 1-500");
    call(&visitor, "hbuild create 8000"); contains("Created room 8000");
    call(&visitor, "hbuild create 8049"); contains("Created room 8049");
    call(&visitor, "hbuild create 8050"); contains("assigned room range");
    call(&visitor, "hbuild name Outside range"); contains("assigned room range");
    call(&visitor, "hdm restore"); contains("Admin permission");
    call(&visitor, "hstaff whoami"); contains("role: player");
    check(hd_build_access(&visitor, 7999) == 0 && hd_build_access(&visitor, 8000) == 1);
    check(hd_build_access(&visitor, 8049) == 1 && hd_build_access(&visitor, 8050) == 0);
    call(&founder, "hbuild unassign Visitor"); contains("revoked immediately"); check(hd_build_access(&visitor, 8000) == 0);
    call(&admin, "hdm goto 20"); contains("Teleported Adminhero to room 20"); check(admin.parent_rom == &second);
    check(admin.class == MAGE && admin.level == 1);
    call(&admin, "hdm restore"); contains("Restored Adminhero"); check(admin.hpcur == 40 && admin.mpcur == 20);
    call(&admin, "hdm restore Visitor"); contains("Owner permission"); check(visitor.hpcur == 1);
    call(&owner, "hdm restore Visitor"); contains("Restored Visitor"); check(visitor.hpcur == 40);
    call(&owner, "hdm restore Realmkeeper"); contains("protected");
    call(&owner, "hdm bring Adminhero"); contains("Teleported Adminhero to room 10"); check(admin.parent_rom == &first);
    call(&founder, "hdm bring Ownerhero"); contains("protected");
    call(&owner, "hdm bring Nobody"); contains("online character");
    memset(&combat, 0, sizeof(combat)); admin.first_enm = &combat;
    call(&admin, "hdm goto 20"); contains("Finish combat"); check(admin.parent_rom == &first); admin.first_enm = NULL;
    memset(&monster, 0, sizeof(monster)); memset(&monster_tag, 0, sizeof(monster_tag));
    strcpy(combat.enemy, admin.name); monster.first_enm = &combat;
    monster_tag.crt = &monster; first.first_mon = &monster_tag;
    call(&admin, "hdm goto 20"); contains("Finish combat"); check(admin.parent_rom == &first);
    first.first_mon = NULL;
    F_SET(&admin, PALIAS); call(&admin, "hdm goto 20"); contains("possessing"); F_CLR(&admin, PALIAS);
    call(&founder, "hstaff audit"); contains("powertry");
    call(&founder, "hstaff revoke Adminhero"); contains("player role");
    call(&founder, "hbuild unassign Adminhero"); contains("revoked immediately");
    previous_writes = writes;
    call(&admin, "hbuild name No longer allowed"); contains("assigned room range"); check(writes == previous_writes);
    call(&admin, "hdm restore"); contains("Admin permission"); check(admin.class == MAGE);
    call(&founder, "hstaff grant Adminhero admin");
    call(&founder, "hbuild assign Adminhero 10 11");
    assert(rename(ROOMPATH "/r00010", ROOMPATH "/original") == 0);
    assert(symlink("original", ROOMPATH "/r00010") == 0);
    call(&admin, "hbuild name Symlink forbidden"); contains("not applied"); check(writes == previous_writes);
    assert(unlink(ROOMPATH "/r00010") == 0); assert(rename(ROOMPATH "/original", ROOMPATH "/r00010") == 0);
    call(&visitor, "hbonus"); contains("No active bonus");
    check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
    call(&visitor, "hbonus start both 1 1"); contains("permission required");
    call(&visitor, "hbonus stop"); contains("permission required");
    {
        creature *actors[] = {&moderator, &implementor, &admin, &founder};
        int factors[] = {5, 5, 10, 20}, durations[] = {60, 60, 1440, 1440};
        int i, j;
        char line[128];
        for (i = 0; i < 4; i++) {
            const char *invalid[] = {"hbonus start both 0 1", "hbonus start both 1 0",
                "hbonus start both 1.5 1", "hbonus start both -1 1", "hbonus start both 2 -1",
                "hbonus start both 2 1 extra", "hbonus start both 2 99999"};
            for (j = 0; j < (int)(sizeof(invalid)/sizeof(invalid[0])); j++) {
                call(actors[i], invalid[j]); contains("Moderators/Implementors: x1-x5");
                check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
            }
            snprintf(line, sizeof(line), "hbonus start both %d 1", factors[i] + 1);
            call(actors[i], line); contains("Moderators/Implementors: x1-x5");
            snprintf(line, sizeof(line), "hbonus start both 1 %d", durations[i] + 1);
            call(actors[i], line); contains("Moderators/Implementors: x1-x5");
            call(actors[i], "hbonus start both 1 1"); contains("Bonus event started");
            call(&visitor, "hbonus"); contains("XP x1; monster gold x1; 1 minute");
            check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
            call(actors[i], "hbonus stop"); contains("stopped");
            snprintf(line, sizeof(line), "hbonus start both %d %d", factors[i], durations[i]);
            call(actors[i], line); contains("Bonus event started");
            check(hd_bonus_gold(100) == 100 * factors[i] && hd_bonus_xp(&visitor, 100) == 100 * factors[i]);
            call(&founder, "hbonus start both 2 1"); contains("already active");
            call(actors[i], "hbonus stop"); contains("stopped");
        }
    }
    call(&moderator, "hbonus start both 5 60"); contains("started");
    call(&implementor, "hbonus stop"); contains("stopped");
    call(&implementor, "hbonus start both 5 60"); contains("started");
    call(&moderator, "hbonus stop"); contains("stopped");
    call(&admin, "hbonus start both 10 1440"); contains("started");
    call(&moderator, "hbonus stop"); contains("creator's rank or higher");
    call(&implementor, "hbonus stop"); contains("creator's rank or higher");
    check(hd_bonus_xp(&visitor, 100) == 1000);
    call(&founder, "hbonus stop"); contains("stopped");
    call(&implementor, "hbonus start both 5 1"); contains("started");
    clock_now += 59; check(hd_bonus_gold(100) == 500);
    clock_now++; check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
    call(&founder, "hbonus start xp 20 1440"); contains("Bonus event started");
    check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 2000);
    call(&admin, "hbonus stop"); contains("creator's rank or higher");
    call(&implementor, "hbonus stop"); contains("creator's rank or higher");
    visitor.experience = 2147483640L;
    check(hd_bonus_xp(&visitor, 100) == 7); check(hd_bonus_xp(&visitor, -1) == 0);
    visitor.experience = 0;
    call(&founder, "hbonus stop"); contains("stopped");
    call(&admin, "hbonus start gold 2 30"); contains("started");
    check(hd_bonus_xp(&visitor, 100) == 100 && hd_bonus_gold(100) == 200);
    check(hd_bonus_gold(2147483640L) == 2147483647L);
    memset(&money, 0, sizeof(money)); money.type = MONEY; money.value = 10;
    visitor.gold = 2147483640L; check(!hd_bonus_can_take_gold(&visitor, &money));
    money.value = 7; check(hd_bonus_can_take_gold(&visitor, &money));
    money.value = -1; check(!hd_bonus_can_take_gold(&visitor, &money));
    visitor.gold = 0;
    /* Persisted role IDs must retain their limits after a fresh load. */
    {
        const char *bad[] = {"HOLLOWDEEP_BONUS 1 6 1 1800100000 1\n",
            "HOLLOWDEEP_BONUS 1 6 1 1800100000 4\n", "HOLLOWDEEP_BONUS 1 11 1 1800100000 2\n",
            "HOLLOWDEEP_BONUS 1 21 1 1800100000 3\n", "HOLLOWDEEP_BONUS 1 2 1 1800100000 5\n",
            "HOLLOWDEEP_BONUS 1 1 1 1800100000 0\n"};
        unsigned int i;
        for (i = 0; i < sizeof(bad)/sizeof(bad[0]); i++) {
            file = fopen("hollowdeep-data/bonus.db", "w"); assert(file); fputs(bad[i], file); fclose(file);
            check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
            call(&founder, "hbonus stop"); contains("unavailable");
        }
    }
    call(&admin, "hstaff revoke Implhero"); contains("now has the player role");
    check(hd_staff_role(&implementor) == HD_ROLE_PLAYER);
    file = fopen("hollowdeep-data/bonus.db", "w"); assert(file); fputs("corrupt", file); fclose(file);
    check(hd_bonus_gold(100) == 100 && hd_bonus_xp(&visitor, 100) == 100);
    call(&founder, "hbonus stop"); contains("unavailable");
    assert(unlink("hollowdeep-data/bonus.db") == 0);
    assert(symlink("../outside", "hollowdeep-data/bonus.db") == 0);
    check(hd_bonus_gold(100) == 100); assert(unlink("hollowdeep-data/bonus.db") == 0);
    file = fopen("hollowdeep-data/builders.db", "w"); assert(file); fputs("corrupt", file); fclose(file);
    check(hd_build_access(&founder, 10) == -1);
    call(&founder, "hbuild name Corrupt ranges"); contains("unavailable"); check(writes == previous_writes);
    assert(unlink("hollowdeep-data/builders.db") == 0);
    call(&founder, "hbuild assign Adminhero 10 11");
    file = fopen("hollowdeep-data/staff.db", "r"); assert(file); saved_size = fread(saved, 1, sizeof(saved), file); fclose(file);
    file = fopen("hollowdeep-data/staff.db", "w"); assert(file); fputs("corrupt", file); fclose(file);
    call(&founder, "hdm restore"); contains("unavailable");
    call(&founder, "hbuild name Fail closed"); contains("unavailable"); check(writes == previous_writes);
    file = fopen("hollowdeep-data/staff.db", "w"); assert(file); assert(fwrite(saved, 1, saved_size, file) == saved_size); fclose(file);
    check(hd_staff_role(&admin) == HD_ROLE_ADMIN);
    assert(chmod("hollowdeep-data", 0500) == 0);
    call(&admin, "hbuild name Audit failed"); contains("audit storage"); check(writes == previous_writes);
    assert(chmod("hollowdeep-data", 0700) == 0);
    file = fopen(PLAYERPATH "/Adminhero", "r"); assert(file); assert(fgets(saved, sizeof(saved), file)); fclose(file);
    check(!strcmp(saved, "saved character sentinel"));
    printf("%d role-based builder and DM checks passed.\n", checks);
    free(first.long_desc);
    return 0;
}
