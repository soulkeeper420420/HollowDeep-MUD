/* Strict native dispatch mock for Round79AC1. No world authentication invented. */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_mount_actions.h"
#include "hd79_mount_store.h"
#include "hd79_mount_presence_store.h"
#include "hd79_presence_dismount_store.h"
#include "hd_mount_travel.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
extern int hd79_mount_command(creature*,cmd*);
static hd79_mount_roster roster;
static hd79_mount_presence presence;
static int have,invalid,writecount;
static char transcript[2048];
void print(int fd,const char *s)
{ (void)fd; if(strlen(transcript)+strlen(s)+1<sizeof transcript)strcat(transcript,s); }
const hd_mount_profile *hd_mount_get(int species)
{static const hd_mount_profile h={1,"Horse",120};return species==1?&h:NULL;}
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{return r&&p&&r->count==p->count&&r->revision==p->revision&&r->active_id==p->active_id;}
int hd79_presence_store_read(const char *name,hd79_mount_roster *r,hd79_mount_presence *p)
{if(strcmp(name,"TestRider")||!have)return HD79_PRESENCE_STORE_ABSENT;if(invalid)return HD79_PRESENCE_STORE_FAILURE;*r=roster;*p=presence;return HD79_PRESENCE_STORE_OK;}
int hd79_presence_dismount_store(const char *name,unsigned room,hd79_mount_roster *out)
{if(strcmp(name,"TestRider")||room!=42||!roster.active_id)return HD79_DISMOUNT_FAILURE;
 writecount++;roster.active_id=0;roster.revision++;presence.active_id=0;presence.revision++;presence.room[0]=room;*out=roster;return HD79_DISMOUNT_SUCCESS;}
int hd79_mount_parse(const char *verb,const char *args,hd79_mount_request *out)
{hd79_mount_request req={0,0};while(*args==' ')args++;
 if(!strcmp(verb,"mount")){if(!strcmp(args,"list")||!*args)req.action=HD79_ACTION_LIST;else if(!strcmp(args,"status"))req.action=HD79_ACTION_STATUS;else if(!strcmp(args,"1")){req.action=HD79_ACTION_BOARD;req.id=1;}}
 else if(!strcmp(verb,"dismount")&&!*args)req.action=HD79_ACTION_DISMOUNT;
 else if(!strcmp(verb,"stable")&&!strcmp(args,"1")){req.action=HD79_ACTION_STABLE;req.id=1;}
 else if(!strcmp(verb,"retrieve")&&!strcmp(args,"1")){req.action=HD79_ACTION_RETRIEVE;req.id=1;}
 if(!req.action)return -1;
 *out=req;
 return 1;}
static void query(creature *p,const char *s,const char *expected)
{cmd c={0};size_t i=0;transcript[0]=0;strcpy(c.fullstr,s);
 while(s[i]&&s[i]!=' '&&i<sizeof c.str[0]-1)i++;
 memcpy(c.str[0],s,i);c.str[0][i]=0;
 hd79_mount_command(p,&c);assert(strstr(transcript,expected));}
int main(void)
{creature p={0};p.type=PLAYER;p.hpcur=10;p.fd=1;p.rom_num=42;p.parent_rom=&p;strcpy(p.name,"TestRider");
 query(&p,"mount list","No mounts registered");assert(!writecount);
 have=1;roster.count=1;roster.active_id=1;roster.revision=5;
 roster.entries[0].id=1;roster.entries[0].species=1;roster.entries[0].endurance=84;
 presence.count=1;presence.active_id=1;presence.revision=5;
 query(&p,"mount status","Riding #1 Horse, Endurance 84/120");
 query(&p,"mount 1","requires native presence/stable verification");
 query(&p,"stable 1","requires native presence/stable verification");
 query(&p,"retrieve 1","requires native presence/stable verification");
 assert(!writecount);
 query(&p,"dismount","Endurance is preserved");
 assert(writecount==1 && roster.active_id==0 && presence.room[0]==42 && roster.entries[0].endurance==84);
 query(&p,"dismount","already on foot");assert(writecount==1);
 invalid=1;query(&p,"mount list","mount record is unavailable");
 query(&p,"mount 0","Usage:");assert(writecount==1);
 puts("PASS: native triple-receipt read/status + one durable dismount");
 puts("PASS: native board/stable/retrieve denied, corrupt records fail closed");
 puts("ROUND79AC1: MOCK NATIVE COMMAND ADAPTER PASS");return 0;}
