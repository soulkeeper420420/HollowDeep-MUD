/* Use actual command names, permission storage and skill handlers. */
#include "mstruct.h"
#include "hollowdeep_help.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_ranges.h"
#include "test_tables.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static char output[8][32768], viewed[256];
static creature players[5];
static int checks;
long hd_staff_test_now(void) { return 1800000000L; }
void print(int fd, const char *format, ...)
{
    va_list args;
    size_t used;
    assert(fd >= 0 && fd < 8);
    used = strlen(output[fd]);
    va_start(args, format);
    vsnprintf(output[fd] + used, sizeof(output[fd]) - used, format, args);
    va_end(args);
}
void view_file(int fd, int param, char *path)
{
    (void)fd; (void)param;
    snprintf(viewed, sizeof(viewed), "%s", path);
}
void broadcast(const char *format, ...) { (void)format; }
void output_buf(void) {}
void disconnect(int fd) { (void)fd; }
creature *find_who(char *name)
{
    int i;
    for (i = 0; i < 5; i++) if (!strcmp(players[i].name, name) && players[i].fd >= 0) return &players[i];
    return NULL;
}
#define check(ok) do { if (!(ok)) { fprintf(stderr, "Failed line %d: %s\n", __LINE__, #ok); exit(1); } checks++; } while (0)
static void has(int fd, const char *text)
{
    if (!strstr(output[fd], text)) { fprintf(stderr, "Missing %s in: %s\n", text, output[fd]); exit(1); }
    checks++;
}
static void run(creature *player, const char *text, int (*handler)(creature *, cmd *))
{
    cmd command;
    memset(&command, 0, sizeof(command));
    snprintf(command.fullstr, sizeof(command.fullstr), "%s", text);
    memset(output, 0, sizeof(output)); viewed[0] = 0;
    handler(player, &command);
}
static void character(creature *p, const char *name, int fd, int class_id)
{
    char path[256]; FILE *file;
    memset(p, 0, sizeof(*p)); strcpy(p->name, name);
    p->type = PLAYER; p->fd = fd; p->class = class_id; p->level = 1;
    snprintf(path, sizeof(path), "%s/%s", PLAYERPATH, name);
    file = fopen(path, "w"); assert(file); fputs("test saved account", file); assert(!fclose(file));
}
static void catalog_check(creature *player)
{
    char all[32768] = "", line[128], needle[128]; int page, i, j, seen;
    for (page = 1; page < 30; page++) {
        snprintf(line, sizeof(line), "help commands %d", page); run(player, line, help);
        if (strstr(output[player->fd], "Choose a page")) break;
        check(strlen(all) + strlen(output[player->fd]) < sizeof(all));
        strcat(all, output[player->fd]);
    }
    check(page < 30);
    for (i = 0; cmdlist[i].cmdno; i++) {
        seen = 0;
        for (j = 0; j < i; j++) if (!strcmp(cmdlist[i].cmdstr, cmdlist[j].cmdstr)) seen = 1;
        if (seen) continue;
        snprintf(needle, sizeof(needle), "  %s\n", cmdlist[i].cmdstr);
        if (cmdlist[i].cmdstr[0] == '*' && !hd_native_command_allowed(player, cmdlist[i].cmdno)) {
            check(!strstr(all, needle)); continue;
        }
        check(strstr(all, needle) != NULL);
        check(strstr(strstr(all, needle) + strlen(needle), needle) == NULL);
        snprintf(line, sizeof(line), "help %s", cmdlist[i].cmdstr); run(player, line, help);
        if (!viewed[0]) fprintf(stderr, "No page for %s: %s\n", line, output[player->fd]);
        check(viewed[0] != 0);
    }
}
int main(int argc, char **argv)
{
    creature *owner = &players[0], *admin = &players[1], *mod = &players[2], *visitor = &players[3], *impl = &players[4], before;
    FILE *file;
    assert(argc == 2 && !chdir(argv[1]) && !mkdir(PLAYERPATH, 0700));
    character(owner, DMNAME, 1, DM); character(admin, "Adminhero", 2, FIGHTER);
    character(mod, "Modhero", 3, FIGHTER); character(visitor, "Visitor", 4, MAGE);
    character(impl, "Implhero", 5, FIGHTER);
    run(owner, "hstaff grant Adminhero admin", hstaff); has(1, "now has the admin role");
    run(admin, "hstaff grant Modhero mod", hstaff); has(2, "now has the mod role");
    run(admin, "hstaff grant Implhero implementor", hstaff); has(2, "now has the implementor role");
    catalog_check(visitor); catalog_check(owner);
    run(visitor, "help wave", help); check(strstr(viewed, "help.100") != NULL);
    run(visitor, "help spell", help); check(strstr(viewed, "help.91") != NULL);
    run(visitor, "help spells", help); check(strstr(viewed, "spellfile") != NULL);
    run(visitor, "help search STAFF", help); has(4, "hstaffclan");
    run(visitor, "help search zzzzzzz", help); has(4, "No matching commands");
    run(visitor, "help commands 0", help); has(4, "help [command]");
    run(visitor, "help commands -1", help); has(4, "help [command]");
    run(visitor, "help commands 9999", help); has(4, "Choose a page");
    run(visitor, "help ../../staff.db", help); check(!viewed[0]);
    run(visitor, "help *memory", help); check(!viewed[0]);
    check(!hd_native_command_allowed(visitor, 149));
    before = *visitor; visitor->class = CARETAKER;
    check(hd_native_command_allowed(visitor, 149)); check(!hd_native_command_allowed(visitor, 148));
    *visitor = before;
    check(!hd_native_command_allowed(owner, 113));
    run(owner, "hstaff grant Visitor owner", hstaff);
    check(!hd_native_command_allowed(visitor, 149));
    run(visitor, "dmcommands", dmcommands); has(4, "x1-x20"); has(4, "Native * commands require");
    run(owner, "hstaff revoke Visitor", hstaff);
    run(visitor, "dmcommands", dmcommands); has(4, "No staff or DM powers assigned");
    run(impl, "dmcommands", dmcommands); has(5, "x1-x5, 1-60"); check(!strstr(output[5], "hstaff audit"));
    run(admin, "dmcommands", dmcommands); has(2, "x1-x10, 1-1440"); check(!strstr(output[2], "hbuild assign"));
    run(owner, "dmcommands native", dmcommands); has(1, "NATIVE DM COMMANDS");
    before = *visitor;
    run(visitor, "skills", skills); has(4, "teach -"); check(!memcmp(visitor, &before, sizeof(before)));
    visitor->class = CLERIC; run(visitor, "skills", skills); has(4, "teach -"); has(4, "turn -");
    visitor->class = FIGHTER; run(visitor, "skills", skills); has(4, "bash -"); has(4, "circle -"); check(!strstr(output[4], "haste -"));
    visitor->class = MONK; visitor->level = 9;
    run(visitor, "skills", skills); has(4, "pick -"); has(4, "sneak -"); check(!strstr(output[4], "touch -"));
    visitor->level = 10; run(visitor, "skills", skills); has(4, "touch -");
    visitor->class = THIEF; run(visitor, "skills", skills); has(4, "peek -");
    visitor->class = ASSASSIN; run(visitor, "skills", skills); check(!strstr(output[4], "peek -"));
    visitor->class = RANGER; run(visitor, "skills", skills); has(4, "track -"); has(4, "haste -");
    run(visitor, "skills all", skills); has(4, "18 skills listed"); has(4, "touch [monk, level 10]");
    run(visitor, "skills all extra", skills); has(4, "skills | skills all");
    *visitor = before;
    run(visitor, "staffclan", staffclan); has(4, "staff role is required");
    check(!strcmp(hd_staff_badge(owner), "[OWNER]")); check(!strcmp(hd_staff_badge(admin), "[ADMIN]"));
    check(!strcmp(hd_staff_badge(mod), "[MOD]")); check(!strcmp(hd_staff_badge(impl), "[IMPLEMENTOR]"));
    check(!strcmp(hd_staff_badge(visitor), ""));
    run(impl, "staffclan say Keep the lantern burning", staffclan);
    has(1, "[IMPLEMENTOR] Implhero: Keep the lantern burning"); has(2, "Keep the lantern burning");
    has(3, "Keep the lantern burning"); has(5, "Keep the lantern burning"); check(!output[4][0]);
    run(admin, "hmoderate mute Implhero 1", hmoderate);
    run(impl, "staffclan say secret muted text", staffclan); has(5, "You are muted"); check(!output[1][0] && !output[2][0] && !output[3][0]);
    run(admin, "hmoderate unmute Implhero", hmoderate);
    run(owner, "hstaff revoke Modhero", hstaff); check(!strcmp(hd_staff_badge(mod), ""));
    run(mod, "staffclan who", staffclan); has(3, "staff role is required");
    run(impl, "staffclan say Private after revocation", staffclan); check(!output[3][0] && !output[4][0]);
    run(owner, "staffclan who", staffclan); has(1, "[IMPLEMENTOR] Implhero"); check(!strstr(output[1], "Modhero"));
    check(hd_build_ranges(owner, "assign", "Visitor 8850 50"));
    check(hd_build_access(visitor, 8850) == 1);
    run(visitor, "staffclan", staffclan); has(4, "staff role is required");
    file = fopen("hollowdeep-data/staff.db", "w"); assert(file); fputs("corrupt", file); assert(!fclose(file));
    run(impl, "staffclan say No leak", staffclan); check(!output[1][0] && !output[2][0]);
    check(!strcmp(hd_staff_badge(impl), ""));
    printf("PASS: %d help, skills, staff-clan and permission assertions\n", checks);
    return 0;
}
