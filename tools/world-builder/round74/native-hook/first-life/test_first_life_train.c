/* Actual command7.c::train() with a test-only stub for VERIFIED remort count.
 * This stub MUST NOT be compiled into real MUD binaries. */
#include "mstruct.h"
#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct {creature *ply; iobuf *io; extra *extr;} Ply[PMAX];
static int raises=0, verified_remorts=-1;
static void must(int ok,const char *why){if(!ok){fprintf(stderr,"FAIL: %s\n",why);exit(1);}}
int hd74_test_verified_remorts(const char *name){
 must(name && strcmp(name,"Hdtrainqa")==0,"look up active trusted native name");
 return verified_remorts;
}
void print(fd,fmt)
int fd;char *fmt;
{(void)fd;(void)fmt;}
void broadcast(fmt)
char *fmt;
{(void)fmt;}
void up_level(creature *p){raises++;p->level++;}
int main(void){
 room room_;creature ply;cmd command_;
 memset(&room_,0,sizeof room_);memset(&ply,0,sizeof ply);memset(&command_,0,sizeof command_);
 ply.type=PLAYER;ply.class=FIGHTER;ply.level=1;ply.fd=5;ply.parent_rom=&room_;
 strcpy(ply.name,"Hdtrainqa");Ply[5].ply=&ply;
 F_SET(&ply,PSECOK);F_SET(&room_,RTRAIN+1);
 /* Fresh first life: half regular XP threshold = 525, gold 525/2 = 262. */
 verified_remorts=0;ply.experience=524;ply.gold=999;
 train(&ply,&command_);
 must(raises==0 && ply.gold==999,"firstlife missing 1 XP refuses without charging");
 ply.experience=525;ply.gold=261;
 train(&ply,&command_);
 must(raises==0 && ply.level==1 && ply.gold==261,"firstlife missing 1 gold refuses");
 ply.gold=262;
 train(&ply,&command_);
 must(raises==1 && ply.level==2 && ply.gold==0,"firstlife train charges 262 gold exactly");
 /* After one remort: no discount, even if level resets to 1. */
 verified_remorts=1;ply.level=1;ply.experience=1049;ply.gold=999;
 train(&ply,&command_);
 must(raises==1 && ply.gold==999,"reborn requires standard 1050 XP");
 ply.experience=1050;ply.gold=524;
 train(&ply,&command_);
 must(raises==1 && ply.gold==524,"reborn requires standard 525 gold");
 ply.gold=525;
 train(&ply,&command_);
 must(raises==2 && ply.level==2 && ply.gold==0,"reborn normal XP/gold train");
 /* Missing trusted record does not magically qualify as first life. */
 verified_remorts=-1;ply.level=1;ply.experience=525;ply.gold=262;
 train(&ply,&command_);
 must(raises==2 && ply.gold==262,"unverified cannot get firstlife discount");
 ply.experience=1050;ply.gold=525;
 train(&ply,&command_);
 must(raises==3 && ply.level==2 && ply.gold==0,"unverified still trains at regular fee");
 verified_remorts=0;ply.level=60;ply.experience=2147483647L;ply.gold=999;
 train(&ply,&command_);
 must(raises==3 && ply.gold==999,"firstlife cap refuses without deducting gold");
 puts("ROUND 74B: actual native train() firstlife/reborn/unknown price and cap PASS");
 return 0;
}
