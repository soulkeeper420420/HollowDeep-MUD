/* Owner-assigned, non-overlapping room ranges, independent of moderation. */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_ranges.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

extern void print(int fd, const char *format, ...);
#define RANGE_MAX 128
struct build_range { char name[20]; int first, last; };
struct range_state { unsigned int count; struct build_range entries[RANGE_MAX]; };

static int load_ranges(struct range_state *state)
{
    int fd, version;
    FILE *file;
    char magic[24], extra;
    unsigned int i, j;
    size_t k, length;
    memset(state, 0, sizeof(*state));
    fd = hd_staff_open_data("builders.db");
    if (fd < 0) return fd == -1;
    file = fdopen(fd, "r");
    if (!file) { close(fd); return 0; }
    if (fscanf(file, "%23s %d %u", magic, &version, &state->count) != 3
            || strcmp(magic, "HOLLOWDEEP_BUILDERS") || version != 1 || state->count > RANGE_MAX) goto bad;
    for (i = 0; i < state->count; i++) {
        struct build_range *range = &state->entries[i];
        if (fscanf(file, "%19s %d %d", range->name, &range->first, &range->last) != 3
                || range->first < 2 || range->last < range->first || range->last >= RMAX) goto bad;
        length = strlen(range->name);
        if (length < 3 || range->name[0] < 'A' || range->name[0] > 'Z') goto bad;
        for (k = 1; k < length; k++) if (range->name[k] < 'a' || range->name[k] > 'z') goto bad;
        for (j = 0; j < i; j++)
            if (range->first <= state->entries[j].last && range->last >= state->entries[j].first) goto bad;
    }
    if (fscanf(file, " %c", &extra) != EOF || ferror(file)) goto bad;
    return fclose(file) == 0;
bad:
    fclose(file); return 0;
}

static int save_ranges(const struct range_state *state)
{
    char text[8192];
    unsigned int i;
    int used = snprintf(text, sizeof(text), "HOLLOWDEEP_BUILDERS 1 %u\n", state->count), n;
    for (i = 0; i < state->count; i++) {
        n = snprintf(text + used, sizeof(text) - (size_t)used, "%s %d %d\n",
                     state->entries[i].name, state->entries[i].first, state->entries[i].last);
        if (n < 0 || (size_t)n >= sizeof(text) - (size_t)used) return 0;
        used += n;
    }
    return hd_staff_write_data("builders.db", text, (unsigned long)used);
}

int hd_build_access(creature *player, int room_number)
{
    struct range_state state;
    unsigned int i;
    int role = hd_staff_role(player);
    if (role < 0 || !load_ranges(&state)) return -1;
    if (role == HD_ROLE_OWNER) return 1;
    for (i = 0; i < state.count; i++)
        if (!strcmp(player->name, state.entries[i].name)
                && (room_number < 0 || (room_number >= state.entries[i].first && room_number <= state.entries[i].last))) return 1;
    return 0;
}

static int integer(const char *text)
{
    const char *p;
    if (!*text || strlen(text) > 4) return -1;
    for (p = text; *p; p++) if (*p < '0' || *p > '9') return -1;
    return atoi(text);
}

int hd_build_ranges(creature *player, const char *action, const char *arguments)
{
    struct range_state state;
    struct build_range *entry;
    char name[20], canonical[20], start[20], count_text[20], extra, value[64];
    int role, words, first = 0, count = 0, last = 0, removed = 0;
    unsigned int i;
    if (strcmp(action, "assign") && strcmp(action, "unassign") && strcmp(action, "ranges") && strcmp(action, "mine")) return 0;
    role = hd_staff_role(player);
    if (role < 0 || !load_ranges(&state)) { print(player->fd, "Builder assignments are unavailable; no building access or changes allowed.\n"); return 1; }
    if (strcmp(action, "mine") && role != HD_ROLE_OWNER) { print(player->fd, "Owner permission required to manage or list all builder ranges. Use hbuild mine for yours.\n"); return 1; }
    if (!strcmp(action, "mine") || !strcmp(action, "ranges")) {
        if (*arguments) goto usage;
        print(player->fd, "BUILDER ROOM RANGES (inclusive)\n");
        for (i = 0; i < state.count; i++)
            if (!strcmp(action, "ranges") || !strcmp(player->name, state.entries[i].name)) {
                print(player->fd, "%s: %d-%d (%d rooms)\n", state.entries[i].name, state.entries[i].first,
                      state.entries[i].last, state.entries[i].last - state.entries[i].first + 1);
                removed++;
            }
        if (!removed) print(player->fd, "No matching assignments.\n");
        if (role == HD_ROLE_OWNER) print(player->fd, "Owners have access to all rooms.\n");
        return 1;
    }
    words = sscanf(arguments, "%19s %19s %19s %c", name, start, count_text, &extra);
    if (!strcmp(action, "unassign")) {
        if (words != 1 || !hd_staff_saved_name(name, canonical)) goto usage;
        for (i = 0; i < state.count;) {
            if (!strcmp(state.entries[i].name, canonical)) {
                memmove(&state.entries[i], &state.entries[i + 1], (--state.count - i) * sizeof(state.entries[0]));
                removed++;
            } else i++;
        }
        if (!removed) { print(player->fd, "That character has no assigned ranges.\n"); return 1; }
        strcpy(value, "revoke");
    } else {
        if ((words != 2 && words != 3) || !hd_staff_saved_name(name, canonical)) goto usage;
        first = integer(start); count = words == 3 ? integer(count_text) : 50;
        last = first + count - 1;
        if (first < 2 || count < 1 || count > 500 || last >= RMAX) goto usage;
        if (state.count == RANGE_MAX) { print(player->fd, "Builder range limit reached.\n"); return 1; }
        for (i = 0; i < state.count; i++)
            if (first <= state.entries[i].last && last >= state.entries[i].first) {
                print(player->fd, "Range overlaps %s's %d-%d assignment.\n", state.entries[i].name, state.entries[i].first, state.entries[i].last); return 1;
            }
        entry = &state.entries[state.count++];
        strcpy(entry->name, canonical); entry->first = first; entry->last = last;
        snprintf(value, sizeof(value), "%d:%d", first, last);
    }
    if (!hd_staff_authorize_action(player, HD_ROLE_OWNER, "rangetry", canonical, value)) return 1;
    if (!save_ranges(&state)) { print(player->fd, "Assignment could not be saved; previous ranges retained.\n"); return 1; }
    if (removed) print(player->fd, "Removed all builder ranges for %s; range access revoked immediately.\n", canonical);
    else print(player->fd, "Assigned %s rooms %d-%d (%d rooms). Existing world content is unchanged.\n", canonical, first, last, count);
    return 1;
usage:
    print(player->fd, "hbuild assign <saved name> <start> [count=50]; count 1-500, rooms 2-8999.\nhbuild unassign <saved name> | ranges | mine\n");
    return 1;
}
