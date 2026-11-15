/* HollowDeep Round 73E: adjustable private wilderness map radius.
 * No creature/object ABI modifications and no treasure reward grants.
 * A radius of 0 disables map rendering; default radius is 3.
 * Unknown / undiscovered tiles remain '?' regardless of radius.
 * Session-only settings reset on server restart/disconnect to a new fd.
 */
#include "mstruct.h"
#include "mextern.h"
#include <stdio.h>
#include <string.h>

#define HD_MAP_MAX_RADIUS 10
#define HD_MAP_DEFAULT_RADIUS 3
#define HD_MAP_MAX_WIDTH 21
#define HD_MAP_SESSIONS 256

struct tile {
    int id, x, y;
    char terrain, region[40], landmark[40];
};

struct hd_map_session {
    int used, fd, radius, showmap;
    char name[80];
};
static struct hd_map_session hd_sessions[HD_MAP_SESSIONS];

static struct hd_map_session *hd_session(creature *player)
{
    struct hd_map_session *slot = 0;
    unsigned long hash = 5381;
    const unsigned char *p;
    size_t length;
    int i;
    if (!player) return 0;
    length = strlen(player->name);
    if (!length || length >= sizeof(hd_sessions[0].name)) return 0;
    for (i = 0; i < HD_MAP_SESSIONS; ++i) {
        if (!hd_sessions[i].used && !slot) slot = &hd_sessions[i];
        if (hd_sessions[i].used && hd_sessions[i].fd == player->fd &&
            !strcmp(hd_sessions[i].name, player->name)) return &hd_sessions[i];
    }
    if (!slot) {
        for (p = (const unsigned char *)player->name; *p; ++p)
            hash = ((hash << 5) + hash) ^ (unsigned long)(*p);
        slot = &hd_sessions[(hash + (unsigned long)(unsigned int)player->fd) % HD_MAP_SESSIONS];
    }
    memset(slot, 0, sizeof *slot);
    slot->used = 1;
    slot->fd = player->fd;
    slot->radius = HD_MAP_DEFAULT_RADIUS;
    strcpy(slot->name, player->name);
    return slot;
}

static int read_tile(FILE *file, struct tile *tile)
{
    char line[160], tail;
    if (!fgets(line, sizeof line, file)) return 0;
    if (!strchr(line, '\n') ||
        sscanf(line, "%5d\t%2d\t%2d\t%c\t%39[A-Za-z0-9 -]\t%39[A-Za-z0-9 -]%c",
               &tile->id, &tile->x, &tile->y, &tile->terrain, tile->region,
               tile->landmark, &tail) != 7 || tail != '\n' ||
        tile->id < 10000 || tile->id >= RMAX ||
        tile->x < 1 || tile->x > 10 || tile->y < 1 || tile->y > 10 ||
        !strchr("F.^S~=#", tile->terrain)) return -1;
    return 1;
}

static int visible(creature *player, int id)
{
    xtag *route;
    for (route = player->parent_rom->first_ext; route; route = route->next_tag)
        if (route->ext->room == id && !F_ISSET(route->ext, XSECRT) &&
            (!F_ISSET(route->ext, XINVIS) || F_ISSET(player, PDINVI))) return 1;
    return 0;
}

static void draw_tile(creature *player, char tile)
{
    const char *code = tile == 'F' ? "32" : tile == '~' ? "34" :
                       tile == '^' ? "37" : tile == 'S' ? "36" :
                       tile == '#' ? "35" : tile == '=' ? "33" : NULL;
    if (code && F_ISSET(player, PANSIC))
        print(player->fd, "\033[%sm%c\033[0m ", code, tile);
    else print(player->fd, "%c ", tile);
}

/* The Mordor parser stores numeric tokens in val[n-1], not str[n].
 * In particular, `mapradius 1` leaves num==1 and str[1] empty, and
 * val[0]==1 is indistinguishable from a no-argument command. Parse the
 * original bounded fullstr to distinguish a query from numeric 0/1.
 * No atoi/atol: reject overflow, extra words and unsupported notation.
 */
int hd_wilderness_mapradius(creature *player, cmd *command)
{
    struct hd_map_session *session;
    const char *cursor, *number;
    size_t width;
    int radius;
    if (!player || !command) return 0;
    session = hd_session(player);
    if (!session) {
        print(player->fd, "Map settings unavailable for this session.\n");
        return 0;
    }
    if (!memchr(command->fullstr, '\0', sizeof(command->fullstr))) {
        print(player->fd, "Use mapradius 0 through 10.\n");
        return 0;
    }
    cursor = command->fullstr;
    while (*cursor == ' ') ++cursor;
    /* Skip the original command word (including legal abbreviations). */
    if (!*cursor || *cursor == '#') {
        print(player->fd, "Use mapradius 0 through 10.\n");
        return 0;
    }
    while (*cursor && *cursor != ' ') ++cursor;
    while (*cursor == ' ') ++cursor;
    if (!*cursor) {
        print(player->fd, "Map radius is %d (0=off, 1-10=range).\n", session->radius);
        return 0;
    }
    number = cursor;
    while (*cursor >= '0' && *cursor <= '9') ++cursor;
    width = (size_t)(cursor - number);
    if (!width || width > 2 || (width > 1 && number[0] == '0')) {
        print(player->fd, "Use mapradius 0 through 10.\n");
        return 0;
    }
    radius = number[0] - '0';
    if (width == 2) radius = radius * 10 + (number[1] - '0');
    while (*cursor == ' ') ++cursor;
    if (*cursor || radius > HD_MAP_MAX_RADIUS) {
        print(player->fd, "Use mapradius 0 through 10.\n");
        return 0;
    }
    session->radius = radius;
    print(player->fd, "Map radius set to %d%s.\n", radius, radius ? "" : " (off)");
    return 0;
}

static int hd_wilderness_draw(creature *player, cmd *command, int quiet)
{
    FILE *file;
    struct tile tile, current;
    struct hd_map_session *session;
    char version[8], grid[HD_MAP_MAX_WIDTH][HD_MAP_MAX_WIDTH];
    char seen[10][10] = {{0}};
    int result, rows = 0, found = 0, x, y, radius, width;
    (void)command;
    if (!player || !player->parent_rom) return 0;
    session = hd_session(player);
    radius = session ? session->radius : HD_MAP_DEFAULT_RADIUS;
    if (!radius) {
        if (!quiet) print(player->fd, "Wilderness map is off. Use mapradius 1-10 to enable.\n");
        return 0;
    }
    width = radius * 2 + 1;
    file = fopen(ROOMPATH "/wilderness.map", "r");
    if (!file) goto unavailable;
    if (!fgets(version, sizeof version, file) || strcmp(version, "HDW1\n")) goto invalid;
    while ((result = read_tile(file, &tile)) > 0) {
        if (++rows > 6000) goto invalid;
        if (tile.id == player->parent_rom->rom_num) {
            if (found) goto invalid;
            current = tile;
            found = 1;
        }
    }
    if (result < 0 || ferror(file) || !found) goto invalid;
    if (fseek(file, 5, SEEK_SET)) goto invalid;
    memset(grid, ' ', sizeof grid);
    rows = 0;
    while ((result = read_tile(file, &tile)) > 0) {
        if (++rows > 6000) goto invalid;
        if (strcmp(current.region, tile.region)) continue;
        if (seen[tile.y - 1][tile.x - 1]++) goto invalid;
        x = tile.x - current.x + radius;
        y = tile.y - current.y + radius;
        if (x >= 0 && x < width && y >= 0 && y < width)
            grid[y][x] = visible(player, tile.id) ? tile.terrain : '?';
    }
    if (result < 0 || ferror(file)) goto invalid;
    fclose(file);
    grid[radius][radius] = '@';
    print(player->fd, "%s (column %d, row %d)\n", current.region, current.x, current.y);
    print(player->fd, "          N\n");
    for (y = 0; y < width; ++y) {
        print(player->fd, "%s", y == radius ? " W  " : "    ");
        for (x = 0; x < width; ++x) draw_tile(player, grid[y][x]);
        print(player->fd, "%s\n", y == radius ? " E" : "");
    }
    print(player->fd, "          S\n");
    print(player->fd, "@ you  ? unscouted  F forest  . plains  ^ mountain\n");
    print(player->fd, "S swamp  ~ river  = road  # ruins\n");
    if (strcmp(current.landmark, "-")) print(player->fd, "Landmark: %s\n", current.landmark);
    return 0;
invalid:
    fclose(file);
unavailable:
    if (!quiet) print(player->fd, "No wilderness map is available here.\n");
    return 0;
}


/* Round 73F: opt-in automatic redraw. All settings are session-only.
 * Native movement dispatch wrappers call the ORIGINAL movement functions,
 * then inspect the room number. No room mutation, parser or save changes.
 * The quiet redraw never announces absent or malformed metadata.
 */
int hd_wilderness_map(creature *player, cmd *command)
{
    return hd_wilderness_draw(player, command, 0);
}

static int hd_same_option(const char *word, size_t count, const char *expected)
{
    size_t i;
    if (strlen(expected) != count) return 0;
    for (i = 0; i < count; ++i) {
        unsigned char c = (unsigned char)word[i];
        if (c >= 'A' && c <= 'Z') c = (unsigned char)(c + ('a' - 'A'));
        if (c != (unsigned char)expected[i]) return 0;
    }
    return 1;
}

/* `showmap` is a toggle; `showmap on|off|toggle|status` are also accepted.
 * The legacy parser keeps text in str[1], but we validate fullstr so
 * extra tokens and malformed input cannot silently change the setting.
 */
int hd_wilderness_showmap(creature *player, cmd *command)
{
    struct hd_map_session *session;
    const char *cursor, *option;
    size_t length;
    int value = -1;
    if (!player || !command) return 0;
    session = hd_session(player);
    if (!session) {
        print(player->fd, "Map settings unavailable for this session.\n");
        return 0;
    }
    if (!memchr(command->fullstr, '\0', sizeof command->fullstr)) goto usage;
    cursor = command->fullstr;
    while (*cursor == ' ') ++cursor;
    if (!*cursor || *cursor == '#') goto usage;
    while (*cursor && *cursor != ' ') ++cursor;
    while (*cursor == ' ') ++cursor;
    if (!*cursor) {
        value = !session->showmap;
    } else {
        option = cursor;
        while (*cursor && *cursor != ' ') ++cursor;
        length = (size_t)(cursor - option);
        while (*cursor == ' ') ++cursor;
        if (*cursor) goto usage;
        if (hd_same_option(option, length, "on")) value = 1;
        else if (hd_same_option(option, length, "off")) value = 0;
        else if (hd_same_option(option, length, "toggle")) value = !session->showmap;
        else if (hd_same_option(option, length, "status")) {
            print(player->fd, "Automatic wilderness map is %s.\n",
                  session->showmap ? "on" : "off");
            return 0;
        } else goto usage;
    }
    session->showmap = value;
    print(player->fd, "Automatic wilderness map is now %s.\n",
          value ? "on" : "off");
    return 0;
usage:
    print(player->fd, "Use showmap on, off, toggle, or status.\n");
    return 0;
}

static void hd_wilderness_after_move(creature *player, int previous_room)
{
    struct hd_map_session *session;
    if (!player || !player->parent_rom) return;
    if (player->rom_num == previous_room) return;
    /* This range is reserved by the verified Round 71 wilderness builder. */
    if (player->rom_num < 10000 || player->rom_num >= RMAX) return;
    session = hd_session(player);
    if (session && session->showmap && session->radius > 0)
        hd_wilderness_draw(player, (cmd *)0, 1);
}

/* A directional command invokes move(), which calls go() internally.
 * A named exit invokes go() directly; neither original function is patched.
 * The wrappers are registered in global.c instead of patching game movement.
 */
extern int move(creature *, cmd *);
extern int go(creature *, cmd *);
int hd_wilderness_move(creature *player, cmd *command)
{
    int previous_room, result;
    if (!player) return 0;
    previous_room = player->rom_num;
    result = move(player, command);
    hd_wilderness_after_move(player, previous_room);
    return result;
}
int hd_wilderness_go(creature *player, cmd *command)
{
    int previous_room, result;
    if (!player) return 0;
    previous_room = player->rom_num;
    result = go(player, command);
    hd_wilderness_after_move(player, previous_room);
    return result;
}
