/* Linux same-directory atomic replacement of bounded, pre-compressed bytes.
 * No untrusted payload paths. This primitive is NOT a complete reward grant;
 * it must never be hooked into a running game without save/receipt integration.
 */
#define _GNU_SOURCE
#include "atomic_player_snapshot.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static int hd_player_name(const char *name) {
    size_t i;
    if (!name || name[0] < 'A' || name[0] > 'Z') return 0;
    for (i = 1; i <= 14U; ++i) {
        if (!name[i]) return i >= 2U;
        if (!((name[i] >= 'A' && name[i] <= 'Z') ||
              (name[i] >= 'a' && name[i] <= 'z'))) return 0;
    }
    return 0;
}
static int hd_target_safe(int dirfd, const char *name) {
    struct stat st;
    if (fstatat(dirfd, name, &st, AT_SYMLINK_NOFOLLOW) == -1)
        return errno == ENOENT;
    /* No symlinks, devices, or hardlinked player saves. */
    return S_ISREG(st.st_mode) && st.st_nlink == 1 && st.st_uid == geteuid();
}
int hd_atomic_player_snapshot(const char *player_dir, const char *player_name,
                              const unsigned char *compressed, size_t size) {
    int dirfd = -1, tmpfd = -1, rc = HD_SNAPSHOT_ERROR;
    char tempname[96] = {0};
    unsigned char random_bytes[12];
    ssize_t nr;
    size_t i, written;
    struct stat dst;
    const char *name = player_name;
    if (!player_dir || !hd_player_name(name) || !compressed ||
        size == 0 || size > HD_PLAYER_COMPRESSED_LIMIT) return HD_SNAPSHOT_ERROR;
    dirfd = open(player_dir, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (dirfd < 0 || fstat(dirfd, &dst) || !S_ISDIR(dst.st_mode) ||
        dst.st_uid != geteuid() || !hd_target_safe(dirfd, name)) goto done;
    /* Random temporary basename: never follow an existing path. */
    {
        int randfd = open("/dev/urandom", O_RDONLY | O_CLOEXEC);
        size_t got = 0;
        if (randfd < 0) goto done;
        while (got < sizeof random_bytes) {
            nr = read(randfd, random_bytes + got, sizeof random_bytes - got);
            if (nr < 0 && errno == EINTR) continue;
            if (nr <= 0) { close(randfd); goto done; }
            got += (size_t)nr;
        }
        if (close(randfd) < 0) goto done;
    }
    if (snprintf(tempname, sizeof tempname, ".%s.", name) < 0) goto done;
    {
        size_t len = strlen(tempname);
        static const char hexdigits[] = "0123456789abcdef";
        if (len + 2U * sizeof(random_bytes) >= sizeof tempname) goto done;
        for (i = 0; i < sizeof random_bytes; ++i) {
            tempname[len++] = hexdigits[random_bytes[i] >> 4];
            tempname[len++] = hexdigits[random_bytes[i] & 15U];
        }
        tempname[len] = '\0';
    }
    tmpfd = openat(dirfd, tempname, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (tmpfd < 0) goto done;
    written = 0;
    while (written < size) {
        size_t take = size - written;
#ifdef HD_ATOMIC_TESTING
        if (take > 7U) take = 7U; /* deterministic partial-write replay */
        if (getenv("HD_ATOMIC_FAIL") && !strcmp(getenv("HD_ATOMIC_FAIL"), "write") &&
            written > 0) goto done;
#endif
        nr = write(tmpfd, compressed + written, take);
        if (nr < 0 && errno == EINTR) continue;
        if (nr <= 0) goto done;
        written += (size_t)nr;
    }
    if (fsync(tmpfd) < 0) goto done;
    if (close(tmpfd) < 0) { tmpfd = -1; goto done; }
    tmpfd = -1;
#ifdef HD_ATOMIC_TESTING
    if (getenv("HD_ATOMIC_FAIL") && !strcmp(getenv("HD_ATOMIC_FAIL"), "before_rename")) goto done;
#endif
    /* Revalidate the existing target immediately before replacement. */
    if (!hd_target_safe(dirfd, name)) goto done;
    if (renameat(dirfd, tempname, dirfd, name) < 0) goto done;
    tempname[0] = '\0'; /* candidate no longer exists */
    rc = HD_SNAPSHOT_UNCERTAIN;
#ifdef HD_ATOMIC_TESTING
    if (getenv("HD_ATOMIC_FAIL") && !strcmp(getenv("HD_ATOMIC_FAIL"), "after_rename")) goto done;
#endif
    if (fsync(dirfd) == 0) rc = HD_SNAPSHOT_OK;
done:
    if (tmpfd >= 0) close(tmpfd);
    if (dirfd >= 0) {
        if (tempname[0]) unlinkat(dirfd, tempname, 0);
        close(dirfd);
    }
    return rc;
}
