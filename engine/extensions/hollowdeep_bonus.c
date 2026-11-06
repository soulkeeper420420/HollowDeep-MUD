/* Persistent, bounded reward events. Apply only to newly earned monster
 * kill XP and newly generated monster gold, never trades or existing coins. */
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hollowdeep_bonus.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

extern void print(int fd, const char *format, ...);
extern void broadcast(const char *format, ...);
#define HD_LONG_MAX 2147483647L
struct bonus_state { int xp, gold, role; unsigned long until; };

static int factor_limit(int role)
{
    switch (role) {
    case HD_ROLE_MOD: case HD_ROLE_IMPLEMENTOR: return 5;
    case HD_ROLE_ADMIN: return 10;
    case HD_ROLE_OWNER: return 20;
    default: return 0;
    }
}

static int minutes_limit(int role)
{
    switch (role) {
    case HD_ROLE_MOD: case HD_ROLE_IMPLEMENTOR: return 60;
    case HD_ROLE_ADMIN: case HD_ROLE_OWNER: return 1440;
    default: return 0;
    }
}

static unsigned long event_time(void)
{
#ifdef HOLLOWDEEP_STAFF_TEST_TIME
    extern long hd_staff_test_now(void);
    long now = hd_staff_test_now();
#else
    time_t now = time(NULL);
#endif
    return now > 0 && (unsigned long)now <= HD_LONG_MAX ? (unsigned long)now : 0;
}

static int load_bonus(struct bonus_state *state)
{
    int fd, version;
    FILE *file;
    char magic[24], extra;
    state->xp = state->gold = 1; state->role = 0; state->until = 0;
    fd = hd_staff_open_data("bonus.db");
    if (fd < 0) return fd == -1;
    file = fdopen(fd, "r");
    if (!file) { close(fd); return 0; }
    if (fscanf(file, "%23s %d %d %d %lu %d", magic, &version, &state->xp, &state->gold, &state->until, &state->role) != 6
            || strcmp(magic, "HOLLOWDEEP_BONUS") || version != 1
            || state->xp < 1 || state->xp > 20 || state->gold < 1 || state->gold > 20
            || state->until > HD_LONG_MAX
            || (!state->until && (state->xp != 1 || state->gold != 1 || state->role))
            || (state->until && (state->xp > factor_limit(state->role)
                                || state->gold > factor_limit(state->role)))
            || fscanf(file, " %c", &extra) != EOF || ferror(file)) {
        fclose(file); return 0;
    }
    return fclose(file) == 0;
}

static int save_bonus(struct bonus_state *state)
{
    char data[128];
    int size = snprintf(data, sizeof(data), "HOLLOWDEEP_BONUS 1 %d %d %lu %d\n",
                        state->xp, state->gold, state->until, state->role);
    return hd_staff_write_data("bonus.db", data, (unsigned long)size);
}

static int integer(const char *text)
{
    const char *p;
    if (!*text || strlen(text) > 4) return -1;
    for (p = text; *p; p++) if (*p < '0' || *p > '9') return -1;
    return atoi(text);
}

int hbonus(creature *player, cmd *command)
{
    struct bonus_state state;
    char verb[25], action[25], kind[25], factor_text[25], minutes_text[25], extra, value[64];
    int words, role, factor, minutes;
    unsigned long now = event_time();
    if (strnlen(command->fullstr, sizeof(command->fullstr)) == sizeof(command->fullstr)) return 0;
    words = sscanf(command->fullstr, "%24s %24s %24s %24s %24s %c", verb, action, kind, factor_text, minutes_text, &extra);
    if (!now || !load_bonus(&state)) {
        print(player->fd, "Bonus event data is unavailable. Normal rewards remain in effect.\n"); return 0;
    }
    if (words == 1 || (words == 2 && !strcmp(action, "status"))) {
        if (state.until <= now) print(player->fd, "No active bonus event. Monster XP x1; monster gold x1.\n");
        else print(player->fd, "BONUS EVENT: monster XP x%d; monster gold x%d; %lu minute(s) remaining.\n", state.xp, state.gold, (state.until - now + 59) / 60);
        return 0;
    }
    role = hd_staff_role(player);
    if (!factor_limit(role)) { print(player->fd, "Moderator or Implementor permission required to manage bonus events.\n"); return 0; }
    if (words == 2 && !strcmp(action, "stop")) {
        if (state.until > now && hd_staff_rank(role) < hd_staff_rank(state.role)) {
            print(player->fd, "Only staff of the event creator's rank or higher may stop this event.\n"); return 0;
        }
        if (!hd_staff_authorize_action(player, HD_ROLE_MOD, "eventtry", player->name, "stop")) return 0;
        state.xp = state.gold = 1; state.until = 0; state.role = 0;
        if (!save_bonus(&state)) { print(player->fd, "Event change could not be saved; previous event retained.\n"); return 0; }
        broadcast("Hollowdeep: %s ended the bonus event. Normal rewards apply.", player->name);
        print(player->fd, "Bonus event stopped.\n"); return 0;
    }
    if (words != 5 || strcmp(action, "start") || (strcmp(kind, "xp") && strcmp(kind, "gold") && strcmp(kind, "both"))) goto usage;
    factor = integer(factor_text); minutes = integer(minutes_text);
    if (factor < 1 || factor > factor_limit(role)
            || minutes < 1 || minutes > minutes_limit(role)
            || now > HD_LONG_MAX - (unsigned long)minutes * 60) goto usage;
    if (state.until > now) { print(player->fd, "An event is already active. Stop it before starting another; bonuses never stack.\n"); return 0; }
    snprintf(value, sizeof(value), "%s%d:%d", kind, factor, minutes);
    if (!hd_staff_authorize_action(player, role, "eventtry", player->name, value)) return 0;
    state.xp = strcmp(kind, "gold") ? factor : 1;
    state.gold = strcmp(kind, "xp") ? factor : 1;
    state.until = now + (unsigned long)minutes * 60; state.role = role;
    if (!save_bonus(&state)) { print(player->fd, "Event change could not be saved; previous event retained.\n"); return 0; }
    broadcast("Hollowdeep: %s started monster XP x%d and monster gold x%d for %d minutes.", player->name, state.xp, state.gold, minutes);
    print(player->fd, "Bonus event started: XP x%d, gold x%d, %d minutes.\n", state.xp, state.gold, minutes);
    return 0;
usage:
    print(player->fd, "hbonus [status] | start <xp|gold|both> <multiplier> <minutes> | stop\nModerators/Implementors: x1-x5, 1-60 minutes.\nAdmins: x1-x10, 1-1440 minutes. Owners: x1-x20, 1-1440 minutes.\n");
    return 0;
}

static long reward(long base, long current, int xp)
{
    struct bonus_state state;
    unsigned long now = event_time();
    long factor = 1, available;
    if (base <= 0 || current < 0 || current >= HD_LONG_MAX) return 0;
    if (now && load_bonus(&state) && state.until > now) factor = xp ? state.xp : state.gold;
    available = HD_LONG_MAX - current;
    return base > available / factor ? available : base * factor;
}

long hd_bonus_xp(creature *player, long base) { return reward(base, player->experience, 1); }
long hd_bonus_gold(long base) { return reward(base, 0, 0); }

int hd_bonus_can_take_gold(creature *player, object *item)
{
    return item->type != MONEY || (item->value >= 0 && player->gold >= 0
            && player->gold <= HD_LONG_MAX && item->value <= HD_LONG_MAX - player->gold);
}
