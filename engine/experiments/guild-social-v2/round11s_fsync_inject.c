/*
 * PRIVATE ROUND11S FAULT INTERPOSER - NEVER LINK/DEPLOY WITH PRODUCTION.
 *
 * One-shot ledger-rename failure and one-shot post-rename directory fsync EIO.
 * Both triggers are disposable marker files inside the isolated chroot.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int rename(const char *from, const char *to)
{
    int (*real_rename)(const char *, const char *);
    real_rename = dlsym(RTLD_NEXT, "rename");
    if (!real_rename) { errno = ENOSYS; return -1; }
    if (to && !strcmp(to, "hollowdeep-data/player-guilds.v1") &&
        unlink("hollowdeep-data/inject-ledger-rename-eio") == 0) {
        errno = EIO;
        return -1;  /* Before primary ledger rename: confirmed precommit failure. */
    }
    return real_rename(from, to);
}

int fsync(int fd)
{
    int (*real_fsync)(int);
    struct stat dir, ledger;
    real_fsync = dlsym(RTLD_NEXT, "fsync");
    if (!real_fsync) { errno = ENOSYS; return -1; }
    /*
     * Distinguish parent-directory fsync from the file fsync.
     * Check for a renamed primary ledger and consume a one-shot marker
     * relative to that directory. This does NOT affect character saves.
     */
    if (fstat(fd, &dir) == 0 && S_ISDIR(dir.st_mode) &&
        fstatat(fd, "player-guilds.v1", &ledger, AT_SYMLINK_NOFOLLOW) == 0 &&
        S_ISREG(ledger.st_mode) &&
        unlinkat(fd, "inject-dir-fsync-eio", 0) == 0) {
        errno = EIO;
        return -1;  /* Rename already occurred: durability UNKNOWN. */
    }
    return real_fsync(fd);
}
