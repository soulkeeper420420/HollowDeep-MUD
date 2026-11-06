/* Searchable help from the registered command table, with role-aware guides. */
#include "mstruct.h"
#include "hollowdeep_help.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_ranges.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

extern void print(int fd, const char *format, ...);
extern void view_file(int fd, int param, char *path);
extern struct { char *cmdstr; int cmdno; int (*cmdfn)(); } cmdlist[];
extern struct { char *splstr; int splno; int (*splfn)(); } spllist[];
#define PAGE_SIZE 30

/* Native DM class checks are separate from HollowDeep staff roles. The one
 * named-operator-only command remains unavailable when DMNAME2 is empty. */
int hd_native_command_allowed(creature *player, int number)
{
    if (!player || player->type != PLAYER || player->class < CARETAKER) return 0;
    switch (number) {
    case 113:
        return player->class >= DM && *DMNAME2 && !strcmp(player->name, DMNAME2);
    case 106: case 119: case 129: case 141: case 144: case 145: case 146: case 148:
        return player->class >= DM;
    default: return number >= 101 && number <= 149;
    }
}

static int words(const cmd *command, char result[5][32])
{
    const unsigned char *p = (const unsigned char *)command->fullstr;
    int count = 0;
    size_t length;
    if (strnlen(command->fullstr, sizeof(command->fullstr)) == sizeof(command->fullstr)) return -1;
    while (*p) {
        while (*p == ' ') p++;
        if (!*p) break;
        if (count == 5) return -1;
        length = 0;
        while (*p && *p != ' ') {
            if (*p < 33 || *p > 126 || length == 31) return -1;
            result[count][length++] = (char)tolower(*p++);
        }
        result[count++][length] = 0;
    }
    return count;
}

static int page_number(const char *text)
{
    const char *p;
    if (!*text || strlen(text) > 4) return 0;
    for (p = text; *p; p++) if (*p < '0' || *p > '9') return 0;
    return atoi(text);
}

static int compare_names(const void *a, const void *b)
{
    return strcmp(*(const char *const *)a, *(const char *const *)b);
}

/* mode 0: reference, 1: socials, 2: native DM commands. Duplicate table
 * entries are removed; registered aliases remain independently searchable. */
static void catalog(creature *player, int mode, const char *query, int page)
{
    const char **names;
    int i, count = 0, total = 0, pages, start, end;
    for (i = 0; cmdlist[i].cmdno; i++) total++;
    names = malloc((size_t)(total ? total : 1) * sizeof(*names));
    if (!names) { print(player->fd, "Command index is temporarily unavailable.\n"); return; }
    for (i = 0; i < total; i++) {
        int native = cmdlist[i].cmdstr[0] == '*';
        if (native && !hd_native_command_allowed(player, cmdlist[i].cmdno)) continue;
        if ((mode == 1 && cmdlist[i].cmdno != 100) || (mode == 2 && !native)) continue;
        if (query && !strstr(cmdlist[i].cmdstr, query)) continue;
        names[count++] = cmdlist[i].cmdstr;
    }
    qsort(names, (size_t)count, sizeof(*names), compare_names);
    total = 0;
    for (i = 0; i < count; i++) if (!total || strcmp(names[i], names[total - 1])) names[total++] = names[i];
    pages = (total + PAGE_SIZE - 1) / PAGE_SIZE;
    if (!total) { print(player->fd, "No matching commands available in this index.\n"); free(names); return; }
    if (page < 1 || page > pages) { print(player->fd, "Choose a page from 1 to %d.\n", pages); free(names); return; }
    print(player->fd, "%s: %d names/aliases. Page %d/%d.\n", mode == 2 ? "NATIVE DM COMMANDS" : "COMMAND INDEX", total, page, pages);
    start = (page - 1) * PAGE_SIZE; end = start + PAGE_SIZE;
    if (end > total) end = total;
    for (i = start; i < end; i++) print(player->fd, "  %s\n", names[i]);
    if (page < pages) {
        if (mode == 2) print(player->fd, "Next: dmcommands native %d\n", page + 1);
        else if (query) print(player->fd, "Next: help search %s %d\n", query, page + 1);
        else print(player->fd, "Next: help %s %d\n", mode == 1 ? "social" : "commands", page + 1);
    }
    print(player->fd, "Details: help <command>. Class, target, equipment and cooldown rules still apply.\n");
    free(names);
}

static int show_page(creature *player, const char *name)
{
    char path[160];
    snprintf(path, sizeof(path), "%s/%s", DOCPATH, name);
    if (access(path, R_OK)) { print(player->fd, "That help page is unavailable; ask the host to check the installed help files.\n"); return 0; }
    view_file(player->fd, 1, path);
    return DOPROMPT;
}

int help(creature *player, cmd *command)
{
    char token[5][32], file[64];
    int count = words(command, token), i, found = 0, number = 0, exact = 0, page = 1;
    if (count == 1) {
        print(player->fd, "HOLLOWDEEP HELP\nhelp <command> | help commands <page> | help search <text> [page]\nhelp social [page] | help spells | help policy | dmcommands | skills\nThis index lists registered commands and aliases; each command enforces its requirements.\n");
        catalog(player, 0, NULL, 1); return 0;
    }
    if (count < 2) goto usage;
    if (!strcmp(token[1], "commands") || !strcmp(token[1], "all") || !strcmp(token[1], "social")) {
        if (count > 3 || (count == 3 && !(page = page_number(token[2])))) goto usage;
        catalog(player, !strcmp(token[1], "social"), NULL, page); return 0;
    }
    if (!strcmp(token[1], "search") && count > 2) {
        if (count < 3 || count > 4 || (count == 4 && !(page = page_number(token[3])))) goto usage;
        catalog(player, 0, token[2], page); return 0;
    }
    if (count != 2) goto usage;
    if (!strcmp(token[1], "spells")) return show_page(player, "spellfile");
    if (!strcmp(token[1], "policy")) return show_page(player, "policy");
    if (!strcmp(token[1], "dm") || !strcmp(token[1], "staff")) {
        cmd guide;
        memset(&guide, 0, sizeof(guide)); strcpy(guide.fullstr, "dmcommands");
        return dmcommands(player, &guide);
    }
    for (i = 0; cmdlist[i].cmdno; i++) {
        if (cmdlist[i].cmdstr[0] == '*' && !hd_native_command_allowed(player, cmdlist[i].cmdno)) continue;
        if (!strcmp(token[1], cmdlist[i].cmdstr)) { number = cmdlist[i].cmdno; found = exact = 1; break; }
        if (!strncmp(cmdlist[i].cmdstr, token[1], strlen(token[1])) && (!found || number != cmdlist[i].cmdno)) {
            found++; number = cmdlist[i].cmdno;
        }
    }
    if (found == 1 || exact) {
        snprintf(file, sizeof(file), "help.%d", number);
        return show_page(player, file);
    }
    if (found > 1) { print(player->fd, "Command is not unique. Use help search %s.\n", token[1]); return 0; }
    for (i = 0; spllist[i].splno != -1; i++) {
        if (!strcmp(token[1], spllist[i].splstr)) { number = spllist[i].splno; found = 1; break; }
        if (!strncmp(spllist[i].splstr, token[1], strlen(token[1]))) { found++; number = spllist[i].splno; }
    }
    if (found == 1) { snprintf(file, sizeof(file), "spell.%d", number); return show_page(player, file); }
    print(player->fd, found ? "Spell name not unique.\n" : "No matching command or spell. Use help search <text>.\n");
    return 0;
usage:
    print(player->fd, "help [command] | commands [page] | social [page] | search <text> [page]\n");
    return 0;
}

int dmcommands(creature *player, cmd *command)
{
    char token[5][32];
    int count = words(command, token), rank = hd_staff_rank(hd_staff_role(player)), build = hd_build_access(player, -1), page = 1;
    if (count >= 2 && !strcmp(token[1], "native")) {
        if (count > 3 || (count == 3 && !(page = page_number(token[2])))) goto usage;
        catalog(player, 2, NULL, page); return 0;
    }
    if (count != 1) goto usage;
    print(player->fd, "YOUR STAFF AND DM COMMANDS\n");
    if (rank < 0) print(player->fd, "Staff roles could not be verified. No role powers are listed.\n");
    if (rank >= 1) {
        print(player->fd, "%s\nhstaff whoami | list\nhmoderate announce | mute | unmute | kick\nstaffclan who | say <message>\nhbuild info\n", hd_staff_badge(player));
        print(player->fd, "hbonus start <xp|gold|both> <multiplier> <minutes> | stop\n");
        print(player->fd, "Your event limits: x1-x%d, 1-%d minutes.\n", rank == 3 ? 20 : rank == 2 ? 10 : 5, rank >= 2 ? 1440 : 60);
    }
    if (rank >= 2) print(player->fd, "hstaff audit | grant <name> <role> | revoke <name>\nhdm goto <room> | restore\n");
    if (rank == 3) print(player->fd, "hbuild assign <name> <start> [count] | unassign <name> | ranges\nhdm bring <name> | restore <name>\n");
    if (build == 1) print(player->fd, "BUILDING: hbuild mine | info | create | name | describe | link | unlink\nhdm goto <room> (assigned rooms; owners have full-world access)\n");
    else if (build < 0) print(player->fd, "Builder assignments could not be verified. No editing powers are listed.\n");
    if (player->class >= CARETAKER) print(player->fd, "NATIVE CLASS POWERS: dmcommands native [page]; help *<command>.\nLegacy target and named-operator restrictions still apply.\n");
    else print(player->fd, "Native * commands require the original caretaker/DM class. A staff role does not grant that class.\n");
    if (rank == 0 && build == 0 && player->class < CARETAKER) print(player->fd, "No staff or DM powers assigned.\n");
    print(player->fd, "Use help <command> for exact syntax. Target hierarchy and room limits still apply.\n");
    return 0;
usage:
    print(player->fd, "dmcommands | dmcommands native [page]\n"); return 0;
}

#define CLASS(c) (1U << (c))
struct hd_skill { const char *name; unsigned int classes; int level; const char *requirement; const char *purpose; };
static const struct hd_skill SKILLS[] = {
    {"backstab", CLASS(THIEF)|CLASS(ASSASSIN), 1, "thief/assassin", "hidden opening strike; suitable weapon required"},
    {"bash", CLASS(FIGHTER)|CLASS(BARBARIAN), 1, "fighter/barbarian", "physical attack that can stun"},
    {"charm", CLASS(BARD), 1, "bard", "charm through song; daily uses and silence apply"},
    {"circle", CLASS(FIGHTER)|CLASS(BARBARIAN), 1, "fighter/barbarian", "confuse an opponent and delay its attacks"},
    {"haste", CLASS(RANGER), 1, "ranger", "temporary dexterity increase"},
    {"hide", 0, 1, "all classes", "conceal yourself or an object"},
    {"meditate", CLASS(MONK), 1, "monk", "attempt to recover health"},
    {"peek", CLASS(THIEF), 1, "thief", "inspect another creature's inventory"},
    {"pick", CLASS(THIEF)|CLASS(MONK), 1, "thief/monk", "attempt to pick a lock"},
    {"pray", CLASS(CLERIC)|CLASS(PALADIN), 1, "cleric/paladin", "temporary piety increase"},
    {"prepare", 0, 1, "all classes", "prepare for traps"},
    {"search", 0, 1, "all classes", "search the room for hidden details"},
    {"sneak", CLASS(THIEF)|CLASS(ASSASSIN)|CLASS(MONK), 1, "thief/assassin/monk", "attempt hidden movement through an exit"},
    {"steal", CLASS(THIEF), 1, "thief", "attempt to take an item from a creature"},
    {"teach", CLASS(MAGE)|CLASS(CLERIC), 1, "mage/cleric", "teach an eligible learned spell to another player"},
    {"touch", CLASS(MONK), 10, "monk, level 10", "touch of death; empty hands and a valid target required"},
    {"track", CLASS(RANGER), 1, "ranger", "read the last creature's direction"},
    {"turn", CLASS(CLERIC)|CLASS(PALADIN), 1, "cleric/paladin", "turn an undead monster"}
};

int skills(creature *player, cmd *command)
{
    char token[5][32];
    int count = words(command, token), all = count == 2 && !strcmp(token[1], "all"), eligible, shown = 0;
    size_t i;
    if (count != 1 && !all) { print(player->fd, "skills | skills all\n"); return 0; }
    print(player->fd, all ? "ALL NATIVE SKILLS\n" : "YOUR AVAILABLE SKILLS (class/level eligibility)\n");
    for (i = 0; i < sizeof(SKILLS)/sizeof(SKILLS[0]); i++) {
        const struct hd_skill *skill = &SKILLS[i];
        eligible = player->type == PLAYER && player->class >= ASSASSIN && player->class <= DM && player->level >= skill->level
                && (!skill->classes || player->class >= CARETAKER || (skill->classes & CLASS(player->class)));
        if (!all && !eligible) continue;
        if (all) print(player->fd, "%s [%s] - %s\n", skill->name, eligible ? "eligible" : skill->requirement, skill->purpose);
        else print(player->fd, "%s - %s\n", skill->name, skill->purpose);
        shown++;
    }
    print(player->fd, "%d skills listed. Use help <skill> for exact rules.\n", shown);
    print(player->fd, "Eligibility is not readiness: cooldowns, equipment, targets and conditions still apply.\nKnown magic: spells. Full skill catalog: skills all. Other commands: help commands.\n");
    return 0;
}
