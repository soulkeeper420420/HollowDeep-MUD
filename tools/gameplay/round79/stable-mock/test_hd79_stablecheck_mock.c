/* Native command wrapper mock, synthetic world registry only. */
#define _GNU_SOURCE
#include "hd_player_store.h"
#include "mextern.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
int hd79_stablecheck(creature *,cmd *);
static char output[300];
void print(int fd,const char *line) { (void)fd; snprintf(output,sizeof output,"%s",line); }
static void query(creature *player,cmd *c,const char *fragment) {
    output[0]=0;
    hd79_stablecheck(player,c);
    assert(strstr(output,fragment));
}
int main(void)
{
    char root[]="/tmp/hd79z-native-test-XXXXXX";
    int fd;
    room actual={2},not_stable={1};
    creature player={0};
    cmd command={0};
    assert(geteuid()==0 && mkdtemp(root)!=NULL && chdir(root)==0);
    assert(mkdir("hollowdeep-data",0755)==0);
    fd=open("hollowdeep-data/mount-stables.hds",O_WRONLY|O_CREAT|O_EXCL,0644);
    assert(fd>=0 && write(fd,"HDST1\n2\n",8)==8 && close(fd)==0);
    player.type=PLAYER;player.hpcur=10;player.rom_num=2;player.parent_rom=&actual;
    strcpy(player.name,"TestRider");
    strcpy(command.fullstr,"stablecheck");strcpy(command.str[0],"stablecheck");
    query(&player,&command,"verified stable");
    player.rom_num=1;player.parent_rom=&not_stable;
    query(&player,&command,"no registered stable");
    player.parent_rom=&actual;
    query(&player,&command,"verification unavailable");
    player.rom_num=2;
    strcpy(command.fullstr,"stablecheck forged");
    query(&player,&command,"verification unavailable");
    puts("ROUND79Z: NATIVE STABLECHECK COMMAND POLICY PASS");
    assert(chdir("/")==0);
    return 0;
}
