/* Round79Z: synthetic root-owned world-only registry tests. */
#define _GNU_SOURCE
#include "hd79_stable_registry.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>

static void write_registry(const char *s)
{
    int fd=open("hollowdeep-data/mount-stables.hds",
                 O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW,0644);
    assert(fd>=0 && write(fd,s,strlen(s))==(ssize_t)strlen(s));
    assert(close(fd)==0);
    assert(chmod("hollowdeep-data/mount-stables.hds",0644)==0);
}
static int check(unsigned room)
{
    return hd79_stable_registry_check("hollowdeep-data",
                                        "mount-stables.hds",room);
}
int main(void)
{
    char root[]="/tmp/hd79z-stable-test-XXXXXX";
    char *dir=mkdtemp(root);
    assert(geteuid()==0 && dir && chdir(dir)==0);
    assert(mkdir("hollowdeep-data",0755)==0);
    assert(check(2)==-1);
    write_registry("HDST1\n2\n10001\n");
    assert(check(2)==1 && check(10001)==1 && check(1)==0);
    assert(check(0)==-1 && check(16777216)==-1);
    assert(hd79_stable_registry_check("..","mount-stables.hds",2)==-1);
    assert(hd79_stable_registry_check("hollowdeep-data","wrong",2)==-1);
    puts("PASS: root-owned stable IDs require verified canonical registry");
    write_registry("HDST1\n2\n2\n"); assert(check(2)==-1);
    write_registry("HDST1\n10001\n2\n"); assert(check(2)==-1);
    write_registry("HDST1\n02\n"); assert(check(2)==-1);
    write_registry("HDST1\n2\r\n"); assert(check(2)==-1);
    write_registry("HDST1\n2\n999999999999\n"); assert(check(2)==-1);
    write_registry("HDST1\n2\njunk\n"); assert(check(2)==-1);
    write_registry("HDST1\n2\n\n"); assert(check(2)==-1);
    puts("PASS: duplicate, disorder, noncanonical, overflow and malformed denied");
    write_registry("HDST1\n2\n");
    assert(chmod("hollowdeep-data/mount-stables.hds",0666)==0);
    assert(check(2)==-1);
    assert(chmod("hollowdeep-data/mount-stables.hds",0644)==0);
    assert(chmod("hollowdeep-data",0777)==0);assert(check(2)==-1);
    assert(chmod("hollowdeep-data",0755)==0);
    assert(unlink("hollowdeep-data/mount-stables.hds")==0);
    assert(symlink("/etc/passwd","hollowdeep-data/mount-stables.hds")==0);
    assert(check(2)==-1);
    assert(unlink("hollowdeep-data/mount-stables.hds")==0);
    write_registry("HDST1\n2\n");assert(check(2)==1);
    puts("PASS: writable registry/dir, missing file and symlink denied");
    assert(unlink("hollowdeep-data/mount-stables.hds")==0);
    assert(rmdir("hollowdeep-data")==0);
    assert(chdir("/")==0 && rmdir(root)==0);
    puts("ROUND79Z: PRIVATE STABLE REGISTRY POLICY PASS");
    return 0;
}
