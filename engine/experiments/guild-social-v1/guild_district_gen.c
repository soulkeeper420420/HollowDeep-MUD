/*
 * HollowDeep guild-district generator -- disposable test-world rooms ONLY.
 * Original standalone C source. Write layout derived from native Mordor 3.00
 * files1.c write_rom / write_obj. Does not use production room paths.
 *
 * IMPORTANT: Native loader acceptance must be proven in a disposable MUD
 * before distributing these room files. Guild halls are NOT access-controlled
 * here; their public entrances intentionally have no exits from the square.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include "mstruct.h"

#ifndef O_NOFOLLOW
#define O_NOFOLLOW 0
#endif
#define BASE_ROOM 6000
#define ROOM_COUNT 12
#define DEED_PRICE 2500L
#define DEED_MAGIC 30001

struct edge { const char *name; int target; };
struct specification {
    const char *title, *description;
    int shop, stock, count;
    struct edge exits[3];
};

static const struct specification specs[ROOM_COUNT] = {
    {"Guild Registry", "A charter counter awaits the founders of new clans.",
      1, 0, 1, {{"east",6002}}},
    {"Guild Registry Stockroom", "Restricted inventory. No public entrance.",
      0, 1, 0, {{NULL,0}}},
    {"Guild District Square", "Banners flutter over the coming guild district.",
      0, 0, 1, {{"west",6000}}},
    {"Starter Hall A Entrance", "An unclaimed private hall entrance.",
      0, 0, 1, {{"east",6004}}},
    {"Starter Hall A Commons", "An unclaimed gathering chamber.",
      0, 0, 2, {{"west",6003},{"north",6005}}},
    {"Starter Hall A Council", "An unclaimed guild council room.",
      0, 0, 1, {{"south",6004}}},
    {"Starter Hall B Entrance", "An unclaimed private hall entrance.",
      0, 0, 1, {{"east",6007}}},
    {"Starter Hall B Commons", "An unclaimed gathering chamber.",
      0, 0, 2, {{"west",6006},{"north",6008}}},
    {"Starter Hall B Council", "An unclaimed guild council room.",
      0, 0, 1, {{"south",6007}}},
    {"Starter Hall C Entrance", "An unclaimed private hall entrance.",
      0, 0, 1, {{"east",6010}}},
    {"Starter Hall C Commons", "An unclaimed gathering chamber.",
      0, 0, 2, {{"west",6009},{"north",6011}}},
    {"Starter Hall C Council", "An unclaimed guild council room.",
      0, 0, 1, {{"south",6010}}}
};
static int put(int fd, const void *ptr, size_t len)
{
    const char *p = (const char *)ptr;
    ssize_t written;
    while (len) {
        written = write(fd, p, len);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) return 0;
        len -= (size_t)written;
        p += written;
    }
    return 1;
}
static int get(int fd, void *ptr, size_t len)
{
    char *p = (char *)ptr;
    ssize_t amount;
    while (len) {
        amount = read(fd, p, len);
        if (amount < 0 && errno == EINTR) continue;
        if (amount <= 0) return 0;
        len -= (size_t)amount;
        p += amount;
    }
    return 1;
}
static int put_int(int fd, int value) { return put(fd, &value, sizeof(value)); }
static int get_int(int fd, int *value) { return get(fd, value, sizeof(*value)); }
static int put_string(int fd, const char *value)
{
    int length = value ? (int)strlen(value)+1 : 0;
    return put_int(fd, length) && (!length || put(fd, value, (size_t)length));
}
static int get_string(int fd)
{
    char string[512];
    int length;
    if (!get_int(fd, &length) || length < 0 || length > (int)sizeof(string)) return 0;
    if (length && (!get(fd, string, (size_t)length) || string[length-1] != 0)) return 0;
    return 1;
}
static int write_one(int dfd, int index)
{
    const struct specification *spec = &specs[index];
    char filename[24];
    int fd, i, zero = 0, item_count;
    room location;
    exit_ route;
    object deed;
    int ok;
    snprintf(filename, sizeof(filename), "r%05d", BASE_ROOM+index);
    fd = openat(dfd, filename, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600);
    if (fd < 0) return 0;
    memset(&location, 0, sizeof(location));
    location.rom_num = BASE_ROOM + index;
    snprintf(location.name, sizeof(location.name), "%s", spec->title);
    if (spec->shop) F_SET(&location, RSHOPP);
    /* Do not link the private starter halls to the public square. */
    ok = put(fd, &location, sizeof(location)) &&
         put_int(fd, spec->count);
    for (i = 0; ok && i < spec->count; i++) {
        memset(&route, 0, sizeof(route));
        snprintf(route.name, sizeof(route.name), "%s", spec->exits[i].name);
        route.room = spec->exits[i].target;
        ok = put(fd, &route, sizeof(route));
    }
    item_count = spec->stock ? 1 : 0;
    ok = ok && put_int(fd, zero) && put_int(fd, item_count);
    if (ok && spec->stock) {
        memset(&deed, 0, sizeof(deed));
        snprintf(deed.name, sizeof(deed.name), "Clan Deed");
        snprintf(deed.description, sizeof(deed.description), "A guild founding charter.");
        snprintf(deed.key[0], sizeof(deed.key[0]), "deed");
        snprintf(deed.key[1], sizeof(deed.key[1]), "charter");
        snprintf(deed.key[2], sizeof(deed.key[2]), "guild");
        deed.value = DEED_PRICE;
        deed.weight = 1;
        deed.special = DEED_MAGIC;
        F_SET(&deed, OPERMT);
        /* Native write_obj emits object bytes then item-container count. */
        ok = put(fd, &deed, sizeof(deed)) && put_int(fd, 0);
    }
    ok = ok && put_string(fd, NULL) &&
         put_string(fd, spec->description) &&
         put_string(fd, NULL) && fsync(fd) == 0;
    if (close(fd)) ok = 0;
    if (!ok) { unlinkat(dfd, filename, 0); return 0; }
    return 1;
}
static int check_one(int dfd, int index)
{
    char filename[24], extra;
    room location;
    exit_ route;
    object deed;
    int fd, i, count, items, nested, ok;
    const struct specification *spec = &specs[index];
    snprintf(filename, sizeof(filename), "r%05d", BASE_ROOM+index);
    fd = openat(dfd, filename, O_RDONLY|O_NOFOLLOW);
    if (fd < 0) return 0;
    ok = get(fd, &location, sizeof(location)) &&
         location.rom_num == BASE_ROOM + index &&
         !strcmp(location.name, spec->title) &&
         (!!F_ISSET(&location,RSHOPP) == !!spec->shop) &&
         get_int(fd, &count) && count == spec->count;
    for (i = 0; ok && i < count; i++) {
        ok = get(fd, &route, sizeof(route)) &&
             !strcmp(route.name, spec->exits[i].name) &&
             route.room == spec->exits[i].target;
    }
    ok = ok && get_int(fd, &count) && count == 0 &&
         get_int(fd, &items) && items == (spec->stock ? 1 : 0);
    if (ok && items) {
        ok = get(fd, &deed, sizeof(deed)) &&
             !strcmp(deed.name, "Clan Deed") &&
             deed.value == DEED_PRICE &&
             deed.special == DEED_MAGIC &&
             F_ISSET(&deed, OPERMT) && get_int(fd, &nested) && nested == 0;
    }
    ok = ok && get_string(fd) && get_string(fd) && get_string(fd);
    if (ok) ok = read(fd, &extra, 1) == 0;
    close(fd);
    return ok;
}
int main(int argc, char **argv)
{
    int dfd, i;
    struct stat st;
    if (argc != 2) {
        fprintf(stderr, "Usage: guild-district-gen EMPTY_PRIVATE_ROOMS_DIRECTORY\n");
        return 2;
    }
    /* Hard-bound this generator to the known private Round 8 workspace. */
    if (strncmp(argv[1], "/root/hollowdeep-dev/guild-social-batch1/round8-", 48) != 0 ||
        strlen(argv[1]) < 17 ||
        strcmp(argv[1] + strlen(argv[1]) - 17, "/test-world/rooms") != 0) {
        fprintf(stderr, "Refusing non-staging output path.\n");
        return 2;
    }
    if (sizeof(room) != 480 || sizeof(exit_) != 44 || sizeof(object) != 352 ||
        sizeof(int) != 4) {
        fprintf(stderr, "Unexpected native 32-bit ABI sizes: room=%lu exit=%lu item=%lu\n",
                (unsigned long)sizeof(room), (unsigned long)sizeof(exit_),
                (unsigned long)sizeof(object));
        return 2;
    }
    if (lstat(argv[1], &st) || !S_ISDIR(st.st_mode) || st.st_uid != geteuid()
        || (st.st_mode & (S_IWGRP|S_IWOTH))) {
        fprintf(stderr, "Refusing unsafe output directory.\n");
        return 2;
    }
    dfd = open(argv[1], O_RDONLY|O_DIRECTORY|O_NOFOLLOW);
    if (dfd < 0) return 2;
    for (i = 0; i < ROOM_COUNT; i++) {
        char filename[24];
        struct stat existing;
        snprintf(filename, sizeof(filename), "r%05d", BASE_ROOM + i);
        if (fstatat(dfd, filename, &existing, AT_SYMLINK_NOFOLLOW) == 0
            || errno != ENOENT) {
            fprintf(stderr, "Refusing existing room: %s\n", filename);
            close(dfd);
            return 2;
        }
    }
    for (i = 0; i < ROOM_COUNT; i++) {
        if (!write_one(dfd, i)) {
            fprintf(stderr, "Write failed at room %d: %s\n", BASE_ROOM+i, strerror(errno));
            close(dfd);
            return 2;
        }
    }
    for (i = 0; i < ROOM_COUNT; i++) {
        if (!check_one(dfd, i)) {
            fprintf(stderr, "Readback failed at room %d\n", BASE_ROOM+i);
            close(dfd);
            return 2;
        }
        printf("PASS room %d: %s\n", BASE_ROOM+i, specs[i].title);
    }
    if (fsync(dfd)) { close(dfd); return 2; }
    close(dfd);
    printf("PASS: 12 private native-format rooms; 1 stock deed at %ld gold\n",
           DEED_PRICE);
    printf("WARNING: Game loader, purchase, ownership and access tests are not yet done.\n");
    return 0;
}
