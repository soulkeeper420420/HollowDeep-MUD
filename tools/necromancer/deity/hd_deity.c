/* HollowDeep: private deity membership and authorized DM assignment.
 * No numeric class-ID or native creature/save ABI changes.
 * Deities are numeric slots pending a canonical pantheon name registry.
 * Requires HD_DEITY_PLAYTEST; this is not a live game feature.
 */
#define _GNU_SOURCE
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hd_deity.h"
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef HD_DEITY_PLAYTEST
#error "Deity assignments can only be built in a guarded private playtest"
#endif
#define HD_DEITY_DB "deities.db"
#define HD_DEITY_RECORDS 128
#define HD_DEITY_BYTES 8192

extern void print(int fd, char *format, ...);

struct deity_entry { char name[20]; unsigned int id; };
struct deity_book { unsigned int count; struct deity_entry entry[HD_DEITY_RECORDS]; };

static int valid_name(const char *name)
{
    size_t i, n;
    if (!name) return 0;
    n = strnlen(name, 20);
    if (n < 3 || n > 19 || name[0] < 'A' || name[0] > 'Z') return 0;
    for (i = 1; i < n; ++i) if (name[i] < 'a' || name[i] > 'z') return 0;
    return 1;
}

/* Accept a complete, unambiguous file only. Corrupt, symlinked, ambiguous
 * or improperly owned storage fails closed (no deity privileges). */
static int read_book(struct deity_book *book)
{
    int fd, rc = -1, i, j;
    FILE *file;
    char line[128], magic[32], extra;
    unsigned version, count;
    if (!book) return -1;
    memset(book, 0, sizeof *book);
    fd = hd_staff_open_data(HD_DEITY_DB);
    if (fd == -1) return 0; /* no assignments yet */
    if (fd < 0) return -1;
    file = fdopen(fd, "r");
    if (!file) { close(fd); return -1; }
    if (!fgets(line, sizeof line, file) ||
        sscanf(line, "%31s %u %u %c", magic, &version, &count, &extra) != 3 ||
        strcmp(magic, "HOLLOWDEEP_DEITIES") || version != 1 ||
        count > HD_DEITY_RECORDS) goto out;
    for (i = 0; i < (int)count; ++i) {
        unsigned int id;
        char name[20];
        if (!fgets(line, sizeof line, file) ||
            sscanf(line, "%19s %u %c", name, &id, &extra) != 2 ||
            !valid_name(name) || id < 1 || id > HD_DEITY_MAX_ID) goto out;
        for (j = 0; j < i; ++j)
            if (!strcmp(book->entry[j].name, name)) goto out;
        strcpy(book->entry[i].name, name);
        book->entry[i].id = id;
    }
    if (fgets(line, sizeof line, file) || ferror(file)) goto out;
    book->count = count;
    rc = 0;
out:
    if (fclose(file) != 0) rc = -1;
    if (rc != 0) memset(book, 0, sizeof *book);
    return rc;
}

static int write_book(const struct deity_book *book)
{
    char buf[HD_DEITY_BYTES];
    int n;
    size_t used = 0, i;
    if (!book || book->count > HD_DEITY_RECORDS) return 0;
    n = snprintf(buf, sizeof buf, "HOLLOWDEEP_DEITIES 1 %u\n", book->count);
    if (n <= 0 || (size_t)n >= sizeof buf) return 0;
    used = (size_t)n;
    for (i = 0; i < book->count; ++i) {
        if (!valid_name(book->entry[i].name) ||
            book->entry[i].id < 1 || book->entry[i].id > HD_DEITY_MAX_ID) return 0;
        n = snprintf(buf + used, sizeof buf - used, "%s %u\n",
                     book->entry[i].name, book->entry[i].id);
        if (n <= 0 || (size_t)n >= sizeof buf - used) return 0;
        used += (size_t)n;
    }
    return hd_staff_write_data(HD_DEITY_DB, buf, (unsigned long)used);
}

int hd_deity_get(const char *name)
{
    struct deity_book book;
    size_t i;
    if (!valid_name(name) || read_book(&book) != 0) return -1;
    for (i = 0; i < book.count; ++i)
        if (!strcmp(name, book.entry[i].name)) return (int)book.entry[i].id;
    return 0;
}
int hd_deity_assigned(const char *name)
{
    return hd_deity_get(name) > 0;
}

/* Parse from original command string: the 1993 parser treats bare numeric
 * arguments as selectors and may suppress them in cmnd->str[]. */
static int parse_words(const cmd *source, char out[4][25])
{
    const char *p, *start;
    size_t size;
    int count = 0;
    if (!source || strnlen(source->fullstr, sizeof(source->fullstr)) ==
                   sizeof(source->fullstr)) return -1;
    p = source->fullstr;
    while (*p) {
        while (*p == ' ') ++p;
        if (!*p) break;
        if (count == 4) return -1;
        start = p;
        while (*p && *p != ' ') {
            if ((unsigned char)*p < 33 || (unsigned char)*p > 126) return -1;
            ++p;
        }
        size = (size_t)(p - start);
        if (!size || size >= sizeof out[0]) return -1;
        memcpy(out[count], start, size);
        out[count][size] = 0;
        ++count;
    }
    return count;
}
static int numeric_id(const char *text, int *id)
{
    char *end;
    unsigned long num;
    if (!text || !*text || !id) return 0;
    /* Disallow signs, leading spaces, silent octal and arbitrary strings. */
    if (strspn(text, "0123456789") != strlen(text)) return 0;
    errno = 0;
    num = strtoul(text, &end, 10);
    if (errno || *end || num > HD_DEITY_MAX_ID) return 0;
    *id = (int)num;
    return 1;
}
static int set_deity(const char *name, int deity)
{
    struct deity_book book;
    size_t i;
    if (!valid_name(name) || deity < 0 || deity > HD_DEITY_MAX_ID ||
        read_book(&book) != 0) return 0;
    for (i = 0; i < book.count; ++i) {
        if (!strcmp(book.entry[i].name, name)) break;
    }
    if (!deity) {
        if (i < book.count) {
            memmove(book.entry+i, book.entry+i+1,
                (book.count-i-1)*sizeof book.entry[0]);
            --book.count;
        }
    } else if (i < book.count) {
        book.entry[i].id = (unsigned)deity;
    } else {
        if (book.count == HD_DEITY_RECORDS) return 0;
        strcpy(book.entry[book.count].name, name);
        book.entry[book.count++].id = (unsigned)deity;
    }
    return write_book(&book);
}

int hd_dm_deity(creature *actor, cmd *command)
{
    char words[4][25] = {{0}}, target[20], label[16];
    int n, id, current, role;
    if (!actor || actor->fd < 0 || actor->type != PLAYER) return 0;
    role = hd_staff_role(actor);
    /* Native DM class is checked twice, here AND in dispatch/help; sidecar
     * admin/owner authority avoids granting staff power to numeric aliases. */
    if (actor->class != DM || hd_staff_rank(role) < hd_staff_rank(HD_ROLE_ADMIN)) {
        print(actor->fd, "DM class and authorized staff admin role required.\n");
        return 0;
    }
    n = parse_words(command, words);
    if (n == 2 && !strcmp(words[1], "list")) {
        print(actor->fd, "Deity IDs: 1-%d (pantheon names pending); 0 = no deity.\n",
              HD_DEITY_MAX_ID);
        return 0;
    }
    if ((n != 2 && n != 3) || strcmp(words[0], "*deity") ||
        !hd_staff_saved_name(words[1], target)) {
        print(actor->fd, "Usage: *deity list | *deity <saved player> [0-16]\n");
        return 0;
    }
    if (n == 2) {
        current = hd_deity_get(target);
        if (current < 0) print(actor->fd, "Deity storage unavailable.\n");
        else print(actor->fd, "%s deity ID: %d.\n", target, current);
        return 0;
    }
    if (!numeric_id(words[2], &id)) {
        print(actor->fd, "Deity ID must be 0-%d.\n", HD_DEITY_MAX_ID);
        return 0;
    }
    /* Require an audit record BEFORE any write; deny on unavailable staff DB. */
    snprintf(label, sizeof label, "deity%d", id);
    if (!hd_staff_authorize_action(actor, HD_ROLE_ADMIN, "powertry", target, label))
        return 0;
    if (!set_deity(target, id)) {
        print(actor->fd, "Deity update failed. No success acknowledged.\n");
        return 0;
    }
    print(actor->fd, "%s deity ID is now %d.\n", target, id);
    return 0;
}
