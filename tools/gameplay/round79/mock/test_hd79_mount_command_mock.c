/* Native command adapter mock. Proves fail-closed world context and raw
 * command parsing but does NOT replace private ELF32 gameplay testing. */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_mount_action_store.h"
#include "hd79_mount_store.h"
#include "hd_mount_travel.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int hd79_mount_command(creature *,cmd *);
static hd79_mount_roster disk;
static int has_record,write_count;
static char transcript[4096];
void print(int fd,const char *line)
{
    (void)fd;
    if (strlen(transcript)+strlen(line)+1<sizeof transcript)
        strcat(transcript,line);
}
const hd_mount_profile *hd_mount_get(int species)
{
    static const hd_mount_profile horse={1,"Horse",120};
    return species==1 ? &horse : NULL;
}
int hd79_mount_store_read(const char *name,hd79_mount_roster *out)
{
    if (strcmp(name,"TestRider")) return -1;
    if (!has_record) return HD79_MOUNT_STORE_ABSENT;
    *out=disk;
    return HD79_MOUNT_STORE_OK;
}
int hd79_mount_action_store(const char *name,const hd79_mount_request *req,
                            const hd79_mount_context *context,hd79_mount_roster *out)
{
    if (strcmp(name,"TestRider") || req->action!=HD79_ACTION_DISMOUNT ||
        !context || context->verified_stable || context->mount_present)
        return HD79_ACTION_STORE_FAILURE;
    ++write_count;
    disk.active_id=0;
    ++disk.revision;
    *out=disk;
    return HD79_ACTION_STORE_OK;
}
int hd79_mount_parse(const char *verb,const char *args,hd79_mount_request *out)
{
    hd79_mount_request req={0,0};
    while (*args==' ') args++;
    if (!strcmp(verb,"mount")) {
        if (!strcmp(args,"list")||!*args) req.action=HD79_ACTION_LIST;
        else if (!strcmp(args,"status")) req.action=HD79_ACTION_STATUS;
        else if (!strcmp(args,"1")) {req.action=HD79_ACTION_BOARD;req.id=1;}
    } else if (!strcmp(verb,"dismount") && !*args)
        req.action=HD79_ACTION_DISMOUNT;
    else if (!strcmp(verb,"stable") && !strcmp(args,"1"))
        {req.action=HD79_ACTION_STABLE;req.id=1;}
    else if (!strcmp(verb,"retrieve") && !strcmp(args,"1"))
        {req.action=HD79_ACTION_RETRIEVE;req.id=1;}
    if (!req.action) return -1;
    *out=req; return 1;
}
static void query(creature *player,const char *words,const char *expected)
{
    cmd command={0};
    size_t i=0;
    transcript[0]=0;
    strcpy(command.fullstr,words);
    while (words[i] && words[i]!=' ' && i<sizeof command.str[0]-1) i++;
    memcpy(command.str[0],words,i);
    command.str[0][i]=0;
    hd79_mount_command(player,&command);
    assert(strstr(transcript,expected)!=NULL);
}
int main(void)
{
    creature p={0};
    p.type=PLAYER;p.hpcur=20;p.fd=1;p.parent_rom=&p;p.rom_num=42;
    strcpy(p.name,"TestRider");
    query(&p,"mount list","No mounts registered");
    assert(write_count==0);
    has_record=1;disk.count=1;disk.revision=1;
    disk.entries[0].id=1;disk.entries[0].species=1;
    disk.entries[0].endurance=84;
    query(&p,"mount list","Horse - Endurance 84/120");
    query(&p,"mount status","traveling on foot");
    query(&p,"mount 1","requires native presence/stable verification");
    query(&p,"stable 1","requires native presence/stable verification");
    query(&p,"retrieve 1","requires native presence/stable verification");
    assert(write_count==0);
    query(&p,"m 1","Usage:");
    assert(write_count==0);
    disk.active_id=1;
    query(&p,"mount status","Riding #1 Horse, Endurance 84/120");
    query(&p,"dismount","Endurance is preserved");
    assert(write_count==1 && disk.active_id==0 && disk.entries[0].endurance==84);
    query(&p,"dismount","already on foot");
    assert(write_count==1);
    puts("PASS: strict native full-command parsing and read-only listing");
    puts("PASS: board/stable/retrieve fail closed without world authority");
    puts("PASS: durable dismount adapter called once and never refills Endurance");
    puts("ROUND79Y: MOCK NATIVE COMMAND ADAPTER PASS");
    return 0;
}
