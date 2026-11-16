#define _GNU_SOURCE
/* Test-only independent receipt verifier for private player files.
 * Return 0 only after directory fsync and an independent legacy compressed
 * player-record decode show this claim and digest on disk.
 */
#include "hd_player_store.h"
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
int main(int argc, char **argv) {
    int dirfd, present;
    struct stat st;
    if (argc != 4) return 2;
    dirfd=open("player",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (dirfd<0) return 2;
    if (fstat(dirfd,&st) || !S_ISDIR(st.st_mode) ||
        st.st_uid!=geteuid() || (st.st_mode&0777)!=0700 ||
        fsync(dirfd)) { close(dirfd); return 2; }
    close(dirfd);
    present=hd_store_read_claim(argv[1],argv[2],argv[3]);
    return present==1 ? 0 : present==0 ? 1 : 2;
}
