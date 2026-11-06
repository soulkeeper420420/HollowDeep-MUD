/* Hollowdeep combat stances for original Mordor 3.00.
 * No serialized player fields, base armor, THAC0, XP or gold are changed.
 * The hit-threshold hook applies only to physical attack calculations.
 */
#include "mstruct.h"
#include "hollowdeep_stance.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>

extern void print(int fd, const char *format, ...);
#ifndef HOLLOWDEEP_DATA_DIR
#define HOLLOWDEEP_DATA_DIR "hollowdeep-data"
#endif
#ifdef HOLLOWDEEP_STANCE_TEST_TIME
extern long hd_stance_test_now(void);
#define STANCE_NOW() hd_stance_test_now()
#else
#define STANCE_NOW() time(NULL)
#endif

#define HD_STANCE_LOCK_SECONDS 20
#define HD_LAST_TIMESTAMP 2147483627UL
#define HD_STANCE_PATH 512
enum { HD_BALANCED, HD_GUARDED, HD_AGGRESSIVE };
static const char *STANCE_NAMES[] = {"balanced", "guarded", "aggressive"};
struct stance_state { int stance; unsigned long changed; };

static int eligible(const creature *player)
{
    return player && player->type == PLAYER && player->class >= ASSASSIN &&
           player->class <= MONK && player->level >= 1;
}

static int stance_power(const creature *player)
{
    if (!eligible(player)) return 0;
    return player->level >= 10 ? 3 : player->level >= 5 ? 2 : 1;
}

static int stance_path(const creature *player, char *path, size_t size)
{
    size_t i, length;
    char name[20]; /* Original login accepts names shorter than 20 letters. */
    if (!eligible(player)) return 0;
    for (length = 0; length < sizeof(player->name) && player->name[length]; length++) ;
    if (length < 3 || length > 19) return 0;
    for (i = 0; i < length; i++) {
        unsigned char c = (unsigned char)player->name[i];
        if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))) return 0;
        name[i] = (char)tolower(c);
    }
    name[length] = '\0';
    return snprintf(path, size, "%s/%s.stance", HOLLOWDEEP_DATA_DIR, name) < (int)size;
}

/* A missing directory/file means the balanced default; invalid data fails closed. */
static int read_stance(const creature *player, struct stance_state *state)
{
    char path[HD_STANCE_PATH], magic[32], value[16], extra;
    unsigned int version;
    struct stat st;
    FILE *file;
    int fd, selected;
    state->stance = HD_BALANCED;
    state->changed = 0;
    if (!stance_path(player, path, sizeof(path))) return 0;
    if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) return errno == ENOENT;
    if (!S_ISDIR(st.st_mode) || S_ISLNK(st.st_mode)) return 0;
    fd = open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return errno == ENOENT;
    if (fstat(fd, &st) < 0 || !S_ISREG(st.st_mode) || st.st_size > 128) { close(fd); return 0; }
    file = fdopen(fd, "r");
    if (!file) { close(fd); return 0; }
    if (fscanf(file, "%31s %u %15s %lu", magic, &version, value, &state->changed) != 4 ||
        strcmp(magic, "HOLLOWDEEP_STANCE") || version != 1 || state->changed > HD_LAST_TIMESTAMP) {
        fclose(file); return 0;
    }
    selected = -1;
    if (!strcmp(value, "balanced")) selected = HD_BALANCED;
    if (!strcmp(value, "guarded")) selected = HD_GUARDED;
    if (!strcmp(value, "aggressive")) selected = HD_AGGRESSIVE;
    if (selected < 0 || fscanf(file, " %c", &extra) != EOF || ferror(file)) { fclose(file); return 0; }
    if (fclose(file) != 0) return 0;
    state->stance = selected;
    return 1;
}

static int write_stance(const creature *player, const struct stance_state *state)
{
    char path[HD_STANCE_PATH], temporary[HD_STANCE_PATH];
    struct stat st;
    FILE *file;
    int fd, ok;
    if (!stance_path(player, path, sizeof(path))) return 0;
    if (lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) {
        if (errno != ENOENT || mkdir(HOLLOWDEEP_DATA_DIR, 0700) < 0 ||
            lstat(HOLLOWDEEP_DATA_DIR, &st) < 0) return 0;
    }
    if (!S_ISDIR(st.st_mode) || S_ISLNK(st.st_mode)) return 0;
    if (snprintf(temporary, sizeof(temporary), "%s/.stance-XXXXXX", HOLLOWDEEP_DATA_DIR) >= (int)sizeof(temporary)) return 0;
    fd = mkstemp(temporary);
    if (fd < 0) return 0;
    file = fdopen(fd, "w");
    if (!file) { close(fd); unlink(temporary); return 0; }
    ok = fprintf(file, "HOLLOWDEEP_STANCE 1 %s %lu\n", STANCE_NAMES[state->stance], state->changed) >= 0;
    if (fflush(file) != 0 || fsync(fd) != 0) ok = 0;
    if (fclose(file) != 0) ok = 0;
    if (!ok || rename(temporary, path) != 0) { unlink(temporary); return 0; }
    return 1;
}

static int attack_modifier(const creature *player)
{
    struct stance_state state;
    int power = stance_power(player);
    if (!power || !read_stance(player, &state)) return 0;
    return state.stance == HD_AGGRESSIVE ? power : state.stance == HD_GUARDED ? -power : 0;
}

int hd_stance_threshold(creature *attacker, creature *defender, int threshold)
{
    /* A lower threshold is easier to hit on the original d20 roll. Aggressive
     * improves accuracy but exposes the same number of points in defense.
     * Guarded does the reverse. Base fields remain untouched and persist as-is.
     */
    return threshold - attack_modifier(attacker) - attack_modifier(defender);
}

static void describe(creature *player, const struct stance_state *state)
{
    int power = stance_power(player);
    print(player->fd, "Combat stance: %s.\n", STANCE_NAMES[state->stance]);
    if (state->stance == HD_AGGRESSIVE)
        print(player->fd, "Physical accuracy +%d; defense -%d.\n", power, power);
    else if (state->stance == HD_GUARDED)
        print(player->fd, "Physical accuracy -%d; defense +%d.\n", power, power);
    else
        print(player->fd, "Normal physical accuracy and defense.\n");
    print(player->fd, "Stance strength: 1 at level 1, 2 at 5, 3 at 10+.\n");
    print(player->fd, "hstance balanced | guarded | aggressive\n");
}

int hstance(creature *player, cmd *command)
{
    struct stance_state state;
    const char *choice = command->num > 1 ? command->str[1] : "status";
    long now;
    long long until, combat_until, remaining;
    int selected = -1, i;
    if (!eligible(player)) {
        print(player->fd, "Combat stances are for adventurers in the ten playable classes.\n"); return 0;
    }
    if (command->num > 2) {
        print(player->fd, "Usage: hstance [status|balanced|guarded|aggressive]\n"); return 0;
    }
    if (!read_stance(player, &state)) {
        print(player->fd, "Your stance could not be read. Combat uses balanced rules; ask the host to check your stance file.\n"); return 0;
    }
    if (!strcmp(choice, "status")) { describe(player, &state); return 0; }
    for (i = 0; i < 3; i++) if (!strcmp(choice, STANCE_NAMES[i])) selected = i;
    if (selected < 0) {
        print(player->fd, "Usage: hstance [status|balanced|guarded|aggressive]\n"); return 0;
    }
    if (selected == state.stance) { describe(player, &state); return 0; }
    now = (long)STANCE_NOW();
    if (now < 0 || (unsigned long)now > HD_LAST_TIMESTAMP) {
        print(player->fd, "The game clock cannot safely record a stance change.\n"); return 0;
    }
    until = (long long)state.changed + HD_STANCE_LOCK_SECONDS;
    combat_until = (long long)player->lasttime[LT_ATTCK].ltime + player->lasttime[LT_ATTCK].interval + HD_STANCE_LOCK_SECONDS;
    if (combat_until > until) until = combat_until;
    combat_until = (long long)player->lasttime[LT_SPELL].ltime + player->lasttime[LT_SPELL].interval + HD_STANCE_LOCK_SECONDS;
    if (combat_until > until) until = combat_until;
    remaining = until - now;
    if (remaining > 0) {
        if (remaining <= 86400)
            print(player->fd, "Wait %ld more seconds before changing stance.\n", (long)remaining);
        else
            print(player->fd, "Your combat or stance timer is in the future; the host must check the game clock.\n");
        return 0;
    }
    state.stance = selected;
    state.changed = (unsigned long)now;
    if (!write_stance(player, &state)) {
        print(player->fd, "Your stance could not be saved. No stance change was applied.\n"); return 0;
    }
    describe(player, &state);
    print(player->fd, "You may change stance after 20 seconds clear of attack and spell cooldowns.\n");
    return 0;
}
