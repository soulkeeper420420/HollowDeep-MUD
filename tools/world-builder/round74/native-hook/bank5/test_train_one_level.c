/* Exercise the actual native command7.c::train() exactly one level per call. */
#include "mstruct.h"
#include "hd74_xp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct {creature *ply; iobuf *io; extra *extr;} Ply[PMAX];
static int raised=0, remorts=0;
static void ck(int ok,const char *msg){if(!ok){fprintf(stderr,"FAIL: %s\n",msg);exit(1);}}
int hd74_test_verified_remorts(const char *name){
    ck(name && strcmp(name,"Hdtrainqa")==0,"server-verified player identity");
    return remorts;
}
void print(fd,fmt)
int fd;char *fmt;
{(void)fd;(void)fmt;}
void broadcast(fmt)
char *fmt;
{(void)fmt;}
void up_level(creature *p){raised++;p->level++;}
static void run_life(int life){
    room rm; creature ply; cmd command;int n;long total=0, goldstart=1000000L;
    memset(&rm,0,sizeof rm);memset(&ply,0,sizeof ply);memset(&command,0,sizeof command);
    ply.type=PLAYER;ply.class=FIGHTER;ply.level=1;ply.fd=5;ply.parent_rom=&rm;
    strcpy(ply.name,"Hdtrainqa");Ply[5].ply=&ply;
    F_SET(&ply,PSECOK);F_SET(&rm,RTRAIN+1);
    remorts=life;
    ply.experience=hd74_xp_bank_limit(1,remorts);
    ply.gold=goldstart;
    for(n=1;n<=5;n++){
        int before=raised;
        long x,fee;
        ck(hd74_training_cost_for_remorts(n,remorts,&x,&fee)==0,"cost lookup");
        ck(ply.experience>=x,"accumulated XP covers next level");
        train(&ply,&command);
        total+=fee;
        ck(raised==before+1 && ply.level==n+1,"exactly ONE level per train invocation");
        ck(ply.gold==goldstart-total,"charged exactly one level's gold on each invocation");
        ck(ply.experience==hd74_xp_bank_limit(1,remorts),"train does not consume stacked XP");
    }
    {int before=raised;long beforegold=ply.gold;
      train(&ply,&command);
      ck(raised==before && ply.level==6 && ply.gold==beforegold,"no sixth train without earning more XP");}
    if(life==0) puts("ROUND 74B: first-life 5 banked levels -> 5 separate train uses, no sixth PASS");
    else puts("ROUND 74B: reborn 5 banked levels -> 5 separate train uses, no sixth PASS");
}
int main(void){run_life(0);run_life(1);return 0;}
