/* Original HollowDeep map command. The portable sidecar leaves room ABI intact. */
#include "mstruct.h"
#include "mextern.h"
#include <stdio.h>
#include <string.h>

#define MAP_SIZE 7
#define MAP_RADIUS (MAP_SIZE / 2)

struct tile {
    int id, x, y;
    char terrain, region[40], landmark[40];
};

static int read_tile(FILE *file, struct tile *tile)
{
    char line[160], tail;
    if (!fgets(line, sizeof line, file))
        return 0;
    if (!strchr(line, '\n') ||
        sscanf(line, "%5d\t%2d\t%2d\t%c\t%39[A-Za-z0-9 -]\t%39[A-Za-z0-9 -]%c",
               &tile->id, &tile->x, &tile->y, &tile->terrain, tile->region,
               tile->landmark, &tail) != 7 || tail != '\n' ||
        tile->id < 10000 || tile->id >= RMAX ||
        tile->x < 1 || tile->x > 10 || tile->y < 1 || tile->y > 10 ||
        !strchr("F.^S~=#", tile->terrain))
        return -1;
    return 1;
}

static int visible(creature *player, int id)
{
    xtag *route;
    for (route = player->parent_rom->first_ext; route; route = route->next_tag)
        if (route->ext->room == id && !F_ISSET(route->ext, XSECRT) &&
            (!F_ISSET(route->ext, XINVIS) || F_ISSET(player, PDINVI)))
            return 1;
    return 0;
}

static void draw_tile(creature *player, char tile)
{
    const char *code = tile == 'F' ? "32" : tile == '~' ? "34" :
                       tile == '^' ? "37" : tile == 'S' ? "36" :
                       tile == '#' ? "35" : tile == '=' ? "33" : NULL;
    if (code && F_ISSET(player, PANSIC))
        print(player->fd, "\033[%sm%c\033[0m ", code, tile);
    else
        print(player->fd, "%c ", tile);
}

int hd_wilderness_map(creature *player, cmd *command)
{
    FILE *file;
    struct tile tile, current;
    char version[8], grid[MAP_SIZE][MAP_SIZE], seen[10][10] = {{0}};
    int result, rows = 0, found = 0, x, y;
    (void)command;
    if (!player || !player->parent_rom) return 0;
    file = fopen(ROOMPATH "/wilderness.map", "r");
    if (!file) goto unavailable;
    if (!fgets(version, sizeof version, file) || strcmp(version, "HDW1\n"))
        goto invalid;
    while ((result = read_tile(file, &tile)) > 0) {
        if (++rows > 6000) goto invalid;
        if (tile.id == player->parent_rom->rom_num) {
            if (found) goto invalid;
            current = tile;
            found = 1;
        }
    }
    if (result < 0 || ferror(file)) goto invalid;
    if (!found) goto invalid;
    if (fseek(file, 5, SEEK_SET)) goto invalid;
    memset(grid, ' ', sizeof grid);
    rows = 0;
    while ((result = read_tile(file, &tile)) > 0) {
        if (++rows > 6000) goto invalid;
        if (strcmp(current.region, tile.region)) continue;
        if (seen[tile.y - 1][tile.x - 1]++) goto invalid;
        x = tile.x - current.x + MAP_RADIUS;
        y = tile.y - current.y + MAP_RADIUS;
        if (x >= 0 && x < MAP_SIZE && y >= 0 && y < MAP_SIZE)
            grid[y][x] = visible(player, tile.id) ? tile.terrain : '?';
    }
    if (result < 0 || ferror(file)) goto invalid;
    fclose(file);
    grid[MAP_RADIUS][MAP_RADIUS] = '@';
    print(player->fd, "%s (column %d, row %d)\n", current.region, current.x, current.y);
    print(player->fd, "          N\n");
    for (y = 0; y < MAP_SIZE; ++y) {
        print(player->fd, "%s", y == MAP_RADIUS ? " W  " : "    ");
        for (x = 0; x < MAP_SIZE; ++x) draw_tile(player, grid[y][x]);
        print(player->fd, "%s\n", y == MAP_RADIUS ? " E" : "");
    }
    print(player->fd, "          S\n");
    print(player->fd, "@ you  ? unscouted  F forest  . plains  ^ mountain\n");
    print(player->fd, "S swamp  ~ river  = road  # ruins\n");
    if (strcmp(current.landmark, "-")) print(player->fd, "Landmark: %s\n", current.landmark);
    return 0;
invalid:
    fclose(file);
unavailable:
    print(player->fd, "No wilderness map is available here.\n");
    return 0;
}
