/* HollowDeep Round 73C: read-only native treasure clue lookup.
 *
 * This feature grants no items, gold, guardian credit or chest access. A
 * registered, specifically named object must be in the current player's
 * physical first_obj inventory to view a clue from the private sidecar.
 * Sidecar rows are created by trusted server code, never from player input.
 * The later claim/inventory integration must separately verify ownership,
 * guardian instance deaths, and durable native item receipts.
 */
#include "mstruct.h"
#include "mextern.h"
#include <ctype.h>
#include <stdio.h>
#include <string.h>

#define HD_LOCATE_PATH ROOMPATH "/treasure_locate.map"
#define HD_MAP_PREFIX "Treasure Map ["
#define HD_ID_SIZE 33
#define HD_ROW_SIZE 512
#define HD_CLUE_SIZE 181
#define HD_MAX_MAPS 100
#define HD_MAX_ROWS 6000

static int hd_id_char(int c)
{
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9') || c == '_' || c == '.' ||
           c == ':' || c == '-';
}

static int hd_token(const char *value, size_t maximum)
{
    size_t size = 0;
    if (!value) return 0;
    while (value[size]) {
        if (size >= maximum || !hd_id_char((unsigned char)value[size]))
            return 0;
        ++size;
    }
    return size >= 3;
}

/* Exact, null-terminated name; no substring/partial keyword matching. */
static int hd_map_id(object *obj, char *id)
{
    const char *end, *start, *suffix;
    size_t length, prefix = sizeof(HD_MAP_PREFIX) - 1;
    if (!obj) return 0;
    end = (const char *)memchr(obj->name, '\0', sizeof(obj->name));
    if (!end) return 0;
    length = (size_t)(end - obj->name);
    if (length <= prefix + 3 || length >= prefix + HD_ID_SIZE + 1 ||
        strncmp(obj->name, HD_MAP_PREFIX, prefix))
        return 0;
    suffix = end - 1;
    if (*suffix != ']') return 0;
    start = obj->name + prefix;
    length = (size_t)(suffix - start);
    if (length >= HD_ID_SIZE || length < 3) return 0;
    memcpy(id, start, length);
    id[length] = '\0';
    return hd_token(id, HD_ID_SIZE - 1);
}

static int hd_read_clue(const char *owner, const char *id, char *clue)
{
    char row[HD_ROW_SIZE], *tab1, *tab2, *newline;
    int found = 0, count = 0, invalid = 0;
    FILE *file = fopen(HD_LOCATE_PATH, "r");
    if (!file) return 0;
    if (!fgets(row, sizeof row, file) || strcmp(row, "HDLOC1\n")) {
        fclose(file);
        return 0;
    }
    while (fgets(row, sizeof row, file)) {
        if (++count > HD_MAX_ROWS) { invalid = 1; break; }
        newline = strchr(row, '\n');
        if (!newline || newline[1] || newline == row) { invalid = 1; break; }
        *newline = '\0';
        tab1 = strchr(row, '\t');
        if (!tab1) { invalid = 1; break; }
        *tab1++ = '\0';
        tab2 = strchr(tab1, '\t');
        if (!tab2) { invalid = 1; break; }
        *tab2++ = '\0';
        if (strchr(tab2, '\t') || !hd_token(row, 79) ||
            !hd_token(tab1, HD_ID_SIZE - 1) ||
            !*tab2 || strlen(tab2) >= HD_CLUE_SIZE) {
            invalid = 1;
            break;
        }
        {
            const unsigned char *p = (const unsigned char *)tab2;
            while (*p) {
                if (*p < 32 || *p > 126) { invalid = 1; break; }
                ++p;
            }
        }
        if (invalid) break;
        if (!strcmp(row, owner) && !strcmp(tab1, id)) {
            if (found) { invalid = 1; break; }
            strcpy(clue, tab2);
            found = 1;
        }
    }
    if (ferror(file)) invalid = 1;
    fclose(file);
    return found && !invalid;
}

int hd_treasure_locate(ply_ptr, cmnd)
creature *ply_ptr;
cmd *cmnd;
{
    otag *tag;
    char selected[HD_ID_SIZE], candidate[HD_ID_SIZE];
    char clue[HD_CLUE_SIZE];
    const char *requested = 0;
    int count = 0, matches = 0;
    if (!ply_ptr || !cmnd) return 0;
    if (cmnd->num >= 2 && cmnd->str[1][0]) {
        requested = cmnd->str[1];
        if (!hd_token(requested, HD_ID_SIZE - 1)) {
            print(ply_ptr->fd, "Specify a valid treasure map identifier.\n");
            return 0;
        }
    }
    selected[0] = '\0';
    for (tag = ply_ptr->first_obj; tag; tag = tag->next_tag) {
        if (++count > 4096) {
            print(ply_ptr->fd, "Your pack contains too many objects to search.\n");
            return 0;
        }
        if (!hd_map_id(tag->obj, candidate)) continue;
        if (requested && strcmp(candidate, requested)) continue;
        if (++matches > HD_MAX_MAPS) {
            print(ply_ptr->fd, "Too many treasure maps are being carried.\n");
            return 0;
        }
        strcpy(selected, candidate);
    }
    if (!matches) {
        print(ply_ptr->fd, "You must carry the matching treasure map to locate its clues.\n");
        return 0;
    }
    if (!requested && matches != 1) {
        print(ply_ptr->fd, "You carry several treasure maps; use locate <map ID>.\n");
        return 0;
    }
    if (requested && matches != 1) {
        print(ply_ptr->fd, "You need exactly one matching treasure map.\n");
        return 0;
    }
    if (!hd_read_clue(ply_ptr->name, selected, clue)) {
        print(ply_ptr->fd, "The markings on that map cannot be deciphered.\n");
        return 0;
    }
    print(ply_ptr->fd, "The treasure map reveals: %s\n", clue);
    return 0;
}
