/* Private test interposer. Kill the server before the selected commit rename. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int rename(const char *from, const char *to)
{
    int (*real_rename)(const char *, const char *) = dlsym(RTLD_NEXT, "rename");
    const char *marker = NULL;
    if (!strcmp(to, "hollowdeep-data/player-guilds.v1"))
        marker = "hollowdeep-data/kill-before-ledger-rename";
    else if (!strncmp(to, "player/Hd", 9))
        marker = "hollowdeep-data/kill-before-character-rename";
    if (marker && unlink(marker) == 0)
        kill(getpid(), SIGKILL);
    return real_rename(from, to);
}
