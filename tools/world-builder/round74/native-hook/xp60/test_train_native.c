/* Executes actual command7.c::train() against isolated Mordor structures. */
#include "mstruct.h"
#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Legacy ABI: references from command7.c are unprototyped externs. */
struct {creature *ply; iobuf *io; extra *extr;} Ply[PMAX];
static int raises=0;
static void must(int value,const char *why) {if(!value){fprintf(stderr,"FAIL: %s\n",why);exit(1);}}
void print(fd,fmt)
int fd; char *fmt;
{(void)fd;(void)fmt;}
void broadcast(fmt)
char *fmt;
{(void)fmt;}
void up_level(creature *p) { raises++; p->level++; }
int main(void) {
    room room_; creature ply; cmd command_; long cost;
    memset(&room_,0,sizeof room_); memset(&ply,0,sizeof ply);memset(&command_,0,sizeof command_);
    ply.type=PLAYER;ply.class=FIGHTER;ply.level=1;ply.experience=0;
    ply.gold=100000000L; ply.fd=5; ply.parent_rom=&room_;strcpy(ply.name,"Hdtrainqa");
    Ply[5].ply=&ply;
    F_SET(&ply,PSECOK);
    /* Training room flags encode exactly the four-bit class ID. */
    F_SET(&room_,RTRAIN+1);
    cost=hd74_xp_for_next(1)/2;
    train(&ply,&command_);
    must(raises==0 && ply.level==1 && ply.gold==100000000L,"cannot train without XP");
    ply.experience=hd74_xp_for_next(1);
    train(&ply,&command_);
    must(raises==1 && ply.level==2 && ply.gold==100000000L-cost,"train grants exactly one level and charges gold");
    ply.level=59;ply.experience=hd74_xp_for_next(59);cost=hd74_xp_for_next(59)/2;
    ply.gold=cost;
    train(&ply,&command_);
    must(raises==2 && ply.level==60 && ply.gold==0,"trained to cap and paid last cost");
    ply.experience=2147483647L;ply.gold=100000000L;
    train(&ply,&command_);
    must(raises==2 && ply.level==60 && ply.gold==100000000L,"no training or gold loss at cap");
    ply.level=61;
    train(&ply,&command_);
    must(raises==2 && ply.level==61 && ply.gold==100000000L,"no training or gold loss above cap");
    puts("ROUND 74B: actual native train() thresholds, charged gold and level-60 hard stop PASS");
    return 0;
}
