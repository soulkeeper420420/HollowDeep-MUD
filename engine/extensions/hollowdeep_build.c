/* Hollowdeep world building and DM tools for original Mordor 3.00.
 * Use the original room serialization and movement routines without changing
 * a character's native class or lending privileges to another command.
 */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_build.h"
#include "hollowdeep_ranges.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

extern void print(int fd, const char *format, ...);
extern int load_rom(int number, room **result);
extern int write_rom(int fd, room *location, int permanent_only);
extern void add_ply_rom(creature *player, room *location);
extern void del_ply_rom(creature *player, room *location);
extern creature *find_who(char *name);

/* Read the original line: Mordor's word parser consumes numbers as selectors
 * and drops articles, both of which would corrupt builder input. */
static int arguments(cmd *command, char *storage, char **action, char **rest)
{
    char *p;
    size_t i, length = strnlen(command->fullstr, sizeof(command->fullstr));
    if (length == sizeof(command->fullstr)) return 0;
    for (i = 0; i < length; i++)
        if ((unsigned char)command->fullstr[i] < 32 || (unsigned char)command->fullstr[i] > 126) return 0;
    memcpy(storage, command->fullstr, length + 1);
    p = storage;
    while (*p && *p != ' ') p++;
    while (*p == ' ') p++;
    *action = p;
    while (*p && *p != ' ') { *p = (char)tolower((unsigned char)*p); p++; }
    if (*p) *p++ = 0;
    while (*p == ' ') p++;
    *rest = p;
    length = strlen(p);
    while (length && p[length - 1] == ' ') p[--length] = 0;
    return 1;
}

static int number(const char *text)
{
    const char *p;
    long value;
    if (!*text || strlen(text) > 4) return -1;
    for (p = text; *p; p++) if (*p < '0' || *p > '9') return -1;
    value = strtol(text, NULL, 10);
    return value >= 1 && value < RMAX ? (int)value : -1;
}

static int permission(creature *player, int required)
{
    int role = hd_staff_role(player);
    if (role < 0) print(player->fd, "Staff data is unavailable; no builder or DM action is allowed.\n");
    else if (hd_staff_rank(role) < hd_staff_rank(required)) print(player->fd, "%s permission required.\n",
                                   required == HD_ROLE_OWNER ? "Owner" : required == HD_ROLE_ADMIN ? "Admin" : "Moderator");
    return hd_staff_rank(role) >= hd_staff_rank(required);
}

static int record(creature *player, int required, const char *action,
                  const char *target, const char *operation, int room_number)
{
    char value[16];
    if (room_number >= 0) snprintf(value, sizeof(value), "%s:%d", operation, room_number);
    else snprintf(value, sizeof(value), "%s", operation);
    return hd_staff_authorize_action(player, required, action, target, value);
}

/* Commit the native room format through a private temporary file. Existing
 * rooms are replaced only after a complete write. Creation never overwrites.
 * Non-permanent mobs/items keep their normal runtime-only behavior. */
static int save_room(room *location, int creating)
{
    char destination[512], temporary[512];
    struct stat st;
    int fd, ok, exists;
    if (location->rom_num < 1 || location->rom_num >= RMAX) return 0;
    if (lstat(ROOMPATH, &st) || !S_ISDIR(st.st_mode) || st.st_uid != geteuid()
            || (st.st_mode & (S_IWGRP | S_IWOTH))) return 0;
    snprintf(destination, sizeof(destination), "%s/r%05d", ROOMPATH, location->rom_num);
    exists = lstat(destination, &st) == 0;
    if ((exists && (creating || !S_ISREG(st.st_mode) || st.st_uid != geteuid()))
            || (!exists && (errno != ENOENT || !creating))) return 0;
    snprintf(temporary, sizeof(temporary), "%s/.hbuild-XXXXXX", ROOMPATH);
    fd = mkstemp(temporary);
    if (fd < 0) return 0;
    ok = write_rom(fd, location, PERMONLY) >= 0 && fsync(fd) == 0;
    if (close(fd)) ok = 0;
    if (ok) ok = creating ? link(temporary, destination) == 0 : rename(temporary, destination) == 0;
    unlink(temporary);
    return ok;
}

static const char *direction(const char *name)
{
    static const char *names[] = {"north", "south", "east", "west", "northeast",
                                 "northwest", "southeast", "southwest", "up", "down"};
    size_t i;
    for (i = 0; i < sizeof(names)/sizeof(names[0]); i++) if (!strcmp(name, names[i])) return names[i];
    return NULL;
}

int hbuild(creature *player, cmd *command)
{
    char storage[256], *action, *rest, *split, *description;
    room *current = player->parent_rom, *destination, candidate;
    xtag *exit_tag, **link_at;
    int id, ok;
    if (!arguments(command, storage, &action, &rest)) {
        print(player->fd, "Use printable text; see help hbuild.\n"); return 0;
    }
    if (!*action || !strcmp(action, "help")) {
        print(player->fd, "HBUILD: mine | info | create <room> | name <text> | describe <text> | link <direction> <room> | unlink <direction>\nBuild only in assigned ranges; owners manage assign/unassign/ranges. Default assignment: 50 rooms.\nChanges save immediately; links are one-way. See help hbuild.\n");
        return 0;
    }
    if (hd_build_ranges(player, action, rest)) return 0;
    id = !strcmp(action, "create") ? number(rest) : current ? current->rom_num : -1;
    ok = hd_build_access(player, id);
    if (ok < 0) { print(player->fd, "Builder assignments or staff data are unavailable; no changes allowed.\n"); return 0; }
    if (!strcmp(action, "info")) {
        if (hd_staff_rank(hd_staff_role(player)) < hd_staff_rank(HD_ROLE_MOD) && hd_build_access(player, -1) != 1) {
            print(player->fd, "Moderator permission or a builder assignment required.\n"); return 0;
        }
    } else if (!ok) {
        print(player->fd, "Building requires an assigned room range. Use hbuild mine; ask an owner to assign rooms.\n"); return 0;
    }
    if (!current || current->rom_num < 1 || current->rom_num >= RMAX) {
        print(player->fd, "Your current room is unavailable for building.\n"); return 0;
    }
    if (!strcmp(action, "info") && !*rest) {
        print(player->fd, "Room %d: %s\n", current->rom_num, current->name);
        for (exit_tag = current->first_ext; exit_tag; exit_tag = exit_tag->next_tag)
            print(player->fd, "  %s -> %d\n", exit_tag->ext->name, exit_tag->ext->room);
        return 0;
    }
    if (!strcmp(action, "create") && (id = number(rest)) >= 2) {
        memset(&candidate, 0, sizeof(candidate));
        candidate.rom_num = id;
        snprintf(candidate.name, sizeof(candidate.name), "New room %d", id);
        if (!record(player, HD_ROLE_PLAYER, "buildtry", player->name, "create", id)) return 0;
        if (save_room(&candidate, 1)) print(player->fd, "Created room %d. Use hdm goto %d to enter it.\n", id, id);
        else print(player->fd, "Room already exists or could not be saved; no existing room was replaced.\n");
        return 0;
    }
    candidate = *current;
    if ((!strcmp(action, "name") || !strcmp(action, "describe")) && *rest) {
        if (strlen(rest) > (!strcmp(action, "name") ? 79U : 180U)) {
            print(player->fd, "Names allow 1-79 characters; descriptions allow 1-180.\n"); return 0;
        }
        description = NULL;
        if (!strcmp(action, "name")) strcpy(candidate.name, rest);
        else {
            description = malloc(strlen(rest) + 2);
            if (!description) { print(player->fd, "Not enough memory; room unchanged.\n"); return 0; }
            sprintf(description, "%s\n", rest);
            candidate.long_desc = description;
        }
        if (!record(player, HD_ROLE_PLAYER, "buildtry", player->name, action, current->rom_num)) {
            free(description); return 0;
        }
        ok = save_room(&candidate, 0);
        if (ok) {
            if (description) free(current->long_desc);
            *current = candidate;
            print(player->fd, "Room %d %s saved.\n", current->rom_num, action);
        } else { free(description); print(player->fd, "Room could not be saved; the edit was not applied.\n"); }
        return 0;
    }
    if (!strcmp(action, "link") || !strcmp(action, "unlink")) {
        split = strchr(rest, ' ');
        if (split) { *split++ = 0; while (*split == ' ') split++; }
        if (!direction(rest) || (!strcmp(action, "link") && (!split || (id = number(split)) < 0))
                || (!strcmp(action, "unlink") && split)) goto usage;
        link_at = &current->first_ext;
        while (*link_at && strcmp((*link_at)->ext->name, rest)) link_at = &(*link_at)->next_tag;
        if (!strcmp(action, "link")) {
            if (hd_build_access(player, id) != 1) { print(player->fd, "The destination must also be in your assigned range; ask an owner to connect it to the public world.\n"); return 0; }
            if (*link_at) { print(player->fd, "That exit already exists. Unlink it explicitly before replacing it.\n"); return 0; }
            if (load_rom(id, &destination) < 0) { print(player->fd, "Destination room does not exist.\n"); return 0; }
            exit_tag = calloc(1, sizeof(*exit_tag));
            if (!exit_tag) return 0;
            exit_tag->ext = calloc(1, sizeof(*exit_tag->ext));
            if (!exit_tag->ext) { free(exit_tag); return 0; }
            strcpy(exit_tag->ext->name, rest);
            exit_tag->ext->room = id;
            if (!record(player, HD_ROLE_PLAYER, "buildtry", player->name, "link", current->rom_num)) {
                free(exit_tag->ext); free(exit_tag); return 0;
            }
            *link_at = exit_tag;
            if (!save_room(current, 0)) {
                *link_at = NULL; free(exit_tag->ext); free(exit_tag);
                print(player->fd, "Exit could not be saved; room unchanged.\n"); return 0;
            }
            print(player->fd, "Exit %s to room %d saved (one-way).\n", rest, id);
        } else {
            if (!*link_at) { print(player->fd, "That exit does not exist.\n"); return 0; }
            if (!record(player, HD_ROLE_PLAYER, "buildtry", player->name, "unlink", current->rom_num)) return 0;
            exit_tag = *link_at;
            *link_at = exit_tag->next_tag;
            if (!save_room(current, 0)) {
                *link_at = exit_tag; print(player->fd, "Exit could not be saved; room unchanged.\n"); return 0;
            }
            free(exit_tag->ext); free(exit_tag);
            print(player->fd, "Exit %s removed and saved.\n", rest);
        }
        return 0;
    }
usage:
    print(player->fd, "Use help hbuild for exact syntax; room numbers must be 2-8999.\n");
    return 0;
}

static creature *target_player(creature *actor, const char *name)
{
    char canonical[20];
    size_t i, length = strlen(name);
    creature *target;
    int role;
    if (length < 3 || length >= sizeof(canonical)) return NULL;
    for (i = 0; i < length; i++) {
        if (!((name[i] >= 'a' && name[i] <= 'z') || (name[i] >= 'A' && name[i] <= 'Z'))) return NULL;
        canonical[i] = (char)(i ? tolower((unsigned char)name[i]) : toupper((unsigned char)name[i]));
    }
    canonical[length] = 0;
    target = find_who(canonical);
    if (!target || target->type != PLAYER) return NULL;
    role = hd_staff_role(target);
    if (target != actor && (role < 0 || hd_staff_rank(role) >= hd_staff_rank(hd_staff_role(actor)) || !strcmp(target->name, DMNAME))) return NULL;
    return target;
}

static int in_combat(creature *player)
{
    ctag *occupant;
    etag *enemy;
    int group;
    if (player->first_enm) return 1;
    /* Mordor keeps monster hostility on the monster, not on its victim. */
    for (group = 0; group < 2; group++) {
        occupant = group ? player->parent_rom->first_ply : player->parent_rom->first_mon;
        for (; occupant; occupant = occupant->next_tag)
            for (enemy = occupant->crt->first_enm; enemy; enemy = enemy->next_tag)
                if (!strcmp(enemy->enemy, player->name)) return 1;
    }
    return 0;
}

int hdm(creature *player, cmd *command)
{
    char storage[256], *action, *rest;
    creature *target = player;
    room *destination = player->parent_rom;
    int id, required;
    if (!arguments(command, storage, &action, &rest)) { print(player->fd, "Use help hdm for syntax.\n"); return 0; }
    if (!*action || !strcmp(action, "help")) {
        print(player->fd, "HDM: goto <room> (assigned builders, or admin+ anywhere), restore (admin+); bring <character>, restore <character> (owner).\nOther targets must be online and below your role. See help hdm.\n"); return 0;
    }
    required = (!strcmp(action, "bring") || (!strcmp(action, "restore") && *rest)) ? HD_ROLE_OWNER : HD_ROLE_ADMIN;
    if (!strcmp(action, "goto") && number(rest) >= 1 && hd_build_access(player, number(rest)) == 1) required = HD_ROLE_PLAYER;
    if (!permission(player, required)) return 0;
    if (!strcmp(action, "goto")) {
        id = number(rest);
        if (id < 0 || load_rom(id, &destination) < 0) { print(player->fd, "Use hdm goto <existing room 2-8999>.\n"); return 0; }
    } else if (!strcmp(action, "bring") || !strcmp(action, "restore")) {
        if (!strcmp(action, "bring") && !*rest) { print(player->fd, "Use hdm bring <character>.\n"); return 0; }
        if (*rest) target = target_player(player, rest);
        if (!target) { print(player->fd, "Target must be an online character below your role; founder and peers are protected.\n"); return 0; }
    } else { print(player->fd, "Use help hdm for exact syntax.\n"); return 0; }
    if (F_ISSET(target, PALIAS) || !target->parent_rom || !destination) {
        print(player->fd, "The target must be in a room and not possessing a creature.\n"); return 0;
    }
    if (!strcmp(action, "restore")) {
        if (target->hpmax <= 0 || target->mpmax < 0) { print(player->fd, "The target's maximum health or mana is invalid.\n"); return 0; }
        if (!record(player, required, "powertry", target->name, "restore", -1)) return 0;
        target->hpcur = target->hpmax; target->mpcur = target->mpmax;
        print(target->fd, "Your health and mana were restored by %s.\n", player->name);
        print(player->fd, "Restored %s. Use save to retain the restored values.\n", target->name);
    } else {
        if (in_combat(target)) { print(player->fd, "Finish combat before teleporting.\n"); return 0; }
        if (!record(player, required, "powertry", target->name, action, destination->rom_num)) return 0;
        if (target->parent_rom != destination) {
            del_ply_rom(target, target->parent_rom);
            add_ply_rom(target, destination);
        }
        print(target->fd, "Teleported by %s to room %d.\n", player->name, destination->rom_num);
        print(player->fd, "Teleported %s to room %d.\n", target->name, destination->rom_num);
    }
    return 0;
}
