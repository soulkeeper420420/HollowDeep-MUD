/* HollowDeep Round 73D: guarded virtual treasure chest (NO loot grants).
 *
 * The chest is not an object in first_obj: get/take/put cannot extract it.
 * This isolated candidate binds exact monster pointers on first OPEN CHEST
 * and accepts only trusted native die() callbacks from the map owner.
 * State is deliberately volatile: game restart relocks the chest. No rewards,
 * sidecar writes, player ABI changes or persistent claim acknowledgements.
 */
#include "mstruct.h"
#include "mextern.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HD_GUARD_PATH ROOMPATH "/treasure_guardians.map"
#define HD_MAX_SITES 128
#define HD_MAX_GUARDS 5
#define HD_MAX_LINES 6000

struct hd_chest_site {
    int room;
    char map[33];
    int n;
    char name[HD_MAX_GUARDS][80];
};
struct hd_chest_state {
    int active, room, n;
    char map[33], owner[80];
    creature *guardian[HD_MAX_GUARDS];
    unsigned char dead[HD_MAX_GUARDS];
};
static struct hd_chest_state hd_chests[HD_MAX_SITES];

extern int openexit();
extern int hd_treasure_has_map(creature *player, const char *map_id);

static int hd_id_character(int c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9') || c == '.' || c == ':' ||
           c == '_' || c == '-';
}
static int hd_map_token(const char *s) {
    size_t i, n;
    if (!s) return 0;
    n = strlen(s);
    if (n < 3 || n >= 33) return 0;
    for (i = 0; i < n; ++i) if (!hd_id_character((unsigned char)s[i])) return 0;
    return 1;
}
static int hd_guard_name(const char *s) {
    size_t i, n;
    if (!s) return 0;
    n = strlen(s);
    if (!n || n >= 80 || s[0] == ' ' || s[n-1] == ' ') return 0;
    for (i = 0; i < n; ++i) if ((unsigned char)s[i] < 32 || (unsigned char)s[i] > 126 || s[i] == '\t') return 0;
    return 1;
}
/* Returns 1 for one validated site, 0 for no site, -1 for corrupt metadata.
 * Full file is inspected; malformed later lines fail closed. */
static int hd_read_site(int room, struct hd_chest_site *site) {
    FILE *fp;
    char line[512], *fields[2 + HD_MAX_GUARDS], *next, *end;
    long id;
    int found = 0, invalid = 0, lines = 0, count, i, j;
    fp = fopen(HD_GUARD_PATH, "r");
    if (!fp) return 0;
    if (!fgets(line, sizeof line, fp) || strcmp(line, "HDGUARD1\n")) { fclose(fp); return -1; }
    while (fgets(line, sizeof line, fp)) {
        if (++lines > HD_MAX_LINES) { invalid = 1; break; }
        end = strchr(line, '\n');
        if (!end || end[1] != '\0') { invalid = 1; break; }
        *end = '\0';
        fields[0] = line;
        count = 1;
        next = line;
        while ((next = strchr(next, '\t')) != NULL) {
            if (count >= 2 + HD_MAX_GUARDS) { invalid = 1; break; }
            *next++ = '\0';
            fields[count++] = next;
        }
        if (invalid) break;
        if (count < 3 || count > 2 + HD_MAX_GUARDS || !fields[0][0]) { invalid = 1; break; }
        id = strtol(fields[0], &end, 10);
        if (*end || id < 10000 || id >= 16000 || !hd_map_token(fields[1])) { invalid = 1; break; }
        for (i = 2; i < count; ++i) {
            if (!hd_guard_name(fields[i])) { invalid = 1; break; }
            for (j = 2; j < i; ++j) if (!strcmp(fields[i], fields[j])) { invalid = 1; break; }
            if (invalid) break;
        }
        if (invalid) break;
        if (id != room) continue;
        if (found) { invalid = 1; break; }
        site->room = (int)id;
        strcpy(site->map, fields[1]);
        site->n = count - 2;
        for (i = 2; i < count; ++i) strcpy(site->name[i - 2], fields[i]);
        found = 1;
    }
    if (ferror(fp)) invalid = 1;
    fclose(fp);
    return invalid ? -1 : found;
}

/* Only one active owner per map and site. This is a safe single-owner
 * prototype, NOT party-shared instancing or respawn/reset support. */
static struct hd_chest_state *hd_active(const struct hd_chest_site *site, const char *owner) {
    int i;
    for (i = 0; i < HD_MAX_SITES; ++i) {
        if (!hd_chests[i].active) continue;
        if (hd_chests[i].room == site->room && !strcmp(hd_chests[i].map, site->map)) {
            return !strcmp(hd_chests[i].owner, owner) ? &hd_chests[i] : NULL;
        }
    }
    return NULL;
}
static int hd_reserved(const struct hd_chest_site *site) {
    int i;
    for (i = 0; i < HD_MAX_SITES; ++i)
        if (hd_chests[i].active && hd_chests[i].room == site->room &&
            !strcmp(hd_chests[i].map, site->map)) return 1;
    return 0;
}
static struct hd_chest_state *hd_bind(const struct hd_chest_site *site, creature *player) {
    struct hd_chest_state *slot = NULL;
    creature *matches[HD_MAX_GUARDS];
    ctag *tag;
    int i, count, j;
    for (i = 0; i < site->n; ++i) {
        count = 0;
        matches[i] = NULL;
        for (tag = player->parent_rom->first_mon; tag; tag = tag->next_tag) {
            if (tag->crt && tag->crt->type == MONSTER && !strcmp(tag->crt->name, site->name[i])) {
                if (++count > 1) return NULL; /* Ambiguous native guardian */
                matches[i] = tag->crt;
            }
        }
        if (count != 1) return NULL;
        for (j = 0; j < i; ++j) if (matches[j] == matches[i]) return NULL;
    }
    for (i = 0; i < HD_MAX_SITES; ++i)
        if (!hd_chests[i].active) { slot = &hd_chests[i]; break; }
    if (!slot) return NULL;
    memset(slot, 0, sizeof *slot);
    slot->active = 1;
    slot->room = site->room;
    slot->n = site->n;
    strcpy(slot->map, site->map);
    strcpy(slot->owner, player->name);
    for (i = 0; i < site->n; ++i) slot->guardian[i] = matches[i];
    return slot;
}

/* Called by the actual native death path before the monster is freed.
 * A pointer to a different copy of the same monster template is rejected. */
void hd_treasure_guardian_death(creature *victim, creature *killer) {
    int i, j;
    if (!victim || victim->type != MONSTER) return;
    for (i = 0; i < HD_MAX_SITES; ++i) {
        if (!hd_chests[i].active) continue;
        for (j = 0; j < hd_chests[i].n; ++j) {
            if (hd_chests[i].guardian[j] != victim) continue;
            hd_chests[i].guardian[j] = NULL; /* never retain a freed pointer */
            hd_chests[i].dead[j] = (killer && killer->type == PLAYER &&
                !strcmp(hd_chests[i].owner, killer->name) &&
                victim->rom_num == hd_chests[i].room && killer->rom_num == hd_chests[i].room);
        }
    }
}

int hd_treasure_open(creature *player, cmd *command) {
    struct hd_chest_site site;
    struct hd_chest_state *state;
    int status, i, remaining = 0;
    if (!player || !command || !player->parent_rom) return 0;
    if (command->num < 2 || strcmp(command->str[1], "chest"))
        return openexit(player, command); /* preserve original door behavior */
    status = hd_read_site(player->rom_num, &site);
    if (!status) return openexit(player, command);
    if (status < 0) {
        print(player->fd, "The treasure chest's magical wards are unreadable.\n");
        return 0;
    }
    if (!hd_treasure_has_map(player, site.map)) {
        print(player->fd, "You must carry the matching treasure map to open this chest.\n");
        return 0;
    }
    state = hd_active(&site, player->name);
    if (!state) {
        if (hd_reserved(&site)) {
            print(player->fd, "Another explorer already holds this chest's ward.\n");
            return 0;
        }
        state = hd_bind(&site, player);
        if (!state) {
            print(player->fd, "The guardian seal cannot be activated; all guardians must be present.\n");
            return 0;
        }
        print(player->fd, "The chest awakens. Its ward binds %d living guardian%s.\n",
              state->n, state->n == 1 ? "" : "s");
    }
    for (i = 0; i < state->n; ++i) if (!state->dead[i]) ++remaining;
    if (remaining) {
        print(player->fd, "The chest remains magically locked: %d guardian%s still hold the seal.\n",
              remaining, remaining == 1 ? "" : "s");
        return 0;
    }
    print(player->fd, "The guardian seals dissolve. The chest opens, but reward delivery is disabled in this test build.\n");
    return 0;
}
