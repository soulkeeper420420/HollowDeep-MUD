/* Disposable filesystem tests: never create player saves on a live host. */
#define _GNU_SOURCE
#include "atomic_player_snapshot.h"
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static void read_match(const char *path, const char *expect) {
    unsigned char b[1024];
    ssize_t n;
    int fd = open(path, O_RDONLY);
    assert(fd >= 0);
    n = read(fd, b, sizeof b);
    assert(n == (ssize_t)strlen(expect));
    assert(memcmp(b, expect, (size_t)n) == 0);
    assert(close(fd) == 0);
}
int main(void) {
    char dir[] = "/tmp/hd-73g-atomic-XXXXXX", name[256];
    const char *old = "OLD-PLAYER", *next = "NEW-PLAYER-COMPRESSED", *last = "COMMITTED-PLAYER";
    int fd;
    assert(mkdtemp(dir) != NULL);
    assert(snprintf(name, sizeof name, "%s/%s", dir, "Example") < (int)sizeof name);
    fd = open(name, O_CREAT | O_EXCL | O_WRONLY, 0600);
    assert(fd >= 0 && write(fd, old, strlen(old)) == (ssize_t)strlen(old) && close(fd) == 0);
    assert(hd_atomic_player_snapshot(dir, "../Example", (const unsigned char *)next, strlen(next)) == HD_SNAPSHOT_ERROR);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)next, 0) == HD_SNAPSHOT_ERROR);
    assert(setenv("HD_ATOMIC_FAIL", "write", 1) == 0);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)next, strlen(next)) == HD_SNAPSHOT_ERROR);
    read_match(name, old);
    assert(setenv("HD_ATOMIC_FAIL", "before_rename", 1) == 0);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)next, strlen(next)) == HD_SNAPSHOT_ERROR);
    read_match(name, old);
    assert(setenv("HD_ATOMIC_FAIL", "after_rename", 1) == 0);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)next, strlen(next)) == HD_SNAPSHOT_UNCERTAIN);
    read_match(name, next); /* reconcile by reading newly committed file */
    assert(unsetenv("HD_ATOMIC_FAIL") == 0);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)last, strlen(last)) == HD_SNAPSHOT_OK);
    read_match(name, last);
    assert(unlink(name) == 0);
    assert(symlink("/tmp/does-not-exist", name) == 0);
    assert(hd_atomic_player_snapshot(dir, "Example", (const unsigned char *)next, strlen(next)) == HD_SNAPSHOT_ERROR);
    assert(unlink(name) == 0 && rmdir(dir) == 0);
    puts("ROUND 73G: private atomic write/short-write/fault/uncertain-rename PASS");
    return 0;
}
