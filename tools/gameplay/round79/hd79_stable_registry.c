/* Round79Z: fail-closed, read-only root-owned stable world authority.
 * The stable registry is deliberately NOT written from any player command.
 * Only a separate trusted operator supplies this world metadata.
 * One root-owned, non-writable-by-others directory and regular file.
 * Strict canonical text: "HDST1\n" followed by ascending room IDs 1..16777215.
 */
#define _GNU_SOURCE
#include "hd79_stable_registry.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>

#define HD79_STABLE_BYTES 1024U
#define HD79_STABLE_COUNT 64U
#define HD79_STABLE_MAX_ROOM 16777215U

static int safe_root_owned(const struct stat *st,int dir)
{
    return st && st->st_uid==0 && !(st->st_mode&022) &&
           (dir ? S_ISDIR(st->st_mode):S_ISREG(st->st_mode));
}
static int read_all(int fd,char buf[HD79_STABLE_BYTES+1],size_t *length)
{
    size_t total=0;
    ssize_t n;
    for (;;) {
        n=read(fd,buf+total,HD79_STABLE_BYTES+1-total);
        if (n<0) {
            if (errno==EINTR) continue;
            return -1;
        }
        if (!n) break;
        total+=(size_t)n;
        if (total>HD79_STABLE_BYTES) return -1;
    }
    buf[total]=0;
    *length=total;
    return 0;
}
static int verify_registry(const char *buf,size_t len,unsigned room)
{
    size_t i=6,start;
    unsigned previous=0,number,count=0;
    int found=0;
    if (len<8 || memcmp(buf,"HDST1\n",6) || buf[len-1]!='\n')
        return -1;
    while(i<len) {
        start=i;
        number=0;
        while(i<len && buf[i]>='0' && buf[i]<='9') {
            if (number>(HD79_STABLE_MAX_ROOM-(unsigned)(buf[i]-'0'))/10U)
                return -1;
            number=number*10U+(unsigned)(buf[i]-'0');
            ++i;
        }
        if(i==start || i>=len || buf[i]!='\n' ||
           (buf[start]=='0') || number<=previous ||
           number>HD79_STABLE_MAX_ROOM || ++count>HD79_STABLE_COUNT)
            return -1;
        if(number==room) found=1;
        previous=number;
        ++i;
    }
    return count ? found:-1;
}
int hd79_stable_registry_check(const char *directory,
                               const char *filename,unsigned room_id)
{
    int dir=-1,fd=-1,result=-1;
    struct stat st;
    char buf[HD79_STABLE_BYTES+1];
    size_t len=0;
    if (!directory || !filename || !room_id ||
        room_id>HD79_STABLE_MAX_ROOM ||
        strcmp(directory,"hollowdeep-data") ||
        strcmp(filename,"mount-stables.hds")) return -1;
    dir=open(directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(dir<0 || fstat(dir,&st) || !safe_root_owned(&st,1)) goto out;
    fd=openat(dir,filename,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if(fd<0 || fstat(fd,&st) || !safe_root_owned(&st,0) ||
       st.st_size<8 || st.st_size>(off_t)HD79_STABLE_BYTES) goto out;
    if(read_all(fd,buf,&len)) goto out;
    if(len!=(size_t)st.st_size || memchr(buf,0,len)) goto out;
    result=verify_registry(buf,len,room_id);
out:
    if(fd>=0) close(fd);
    if(dir>=0) close(dir);
    return result;
}
