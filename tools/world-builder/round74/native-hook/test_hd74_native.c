#include "mstruct.h"
#include "hd74_native.h"
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

static char transcript[8192];
void print(int fd, const char *fmt, ...)
{
    va_list args;
    size_t used=strlen(transcript);
    (void)fd;
    va_start(args,fmt);
    vsnprintf(transcript+used,sizeof transcript-used,fmt,args);
    va_end(args);
}
static void ck(int cond,const char *desc) {
    if(!cond) {fprintf(stderr,"FAIL: %s\n",desc);exit(1);}
}
static void ok(const char *str,int want) {
    int v[5]={-1,-1,-1,-1,-1};
    int r=hd74_parse_starting_stats(str,v);
    ck(r==want,str);
    if(want) {
        int sum=0,i;
        for(i=0;i<5;i++) {ck(v[i]>=3&&v[i]<=18,"stat bounds");sum+=v[i];}
        ck(sum<=65,"stat pool limit");
    } else ck(v[0]==-1,"invalid input leaves output untouched");
}
int main(void) {
    creature p;
    int i;
    ok("18 18 18 8 3",1);      /* exactly 65 */
    ok("\t18 18 18 8 3\t ",1);
    ok("13 13 13 13 13",1);   /* exactly 65 */
    ok("10 10 10 10 10",1);   /* under cap, legacy rule */
    ok("3 3 3 3 3",1);        /* legacy minimum */
    ok("18 18 18 9 3",0);    /* total 66, rejected */
    ok("2 18 18 18 3",0);    /* below 3 */
    ok("19 18 18 3 3",0);    /* above 18 */
    ok("18 18 18 8 3 3",0);  /* extra token */
    ok("18 18 18 8",0);      /* insufficient tokens */
    ok("18 18 -18 8 3",0);
    ok("18 18 +18 8 3",0);
    ok("18 18 18 8 3abc",0);
    ok("18 18 18 8 3\n",0);
    ok("1000000000000000000000 18 18 8 3",0);
    ok("",0);
    ck(!hd74_parse_starting_stats(0,(int[5]){0}),"null text");
    ck(!hd74_parse_starting_stats("18 18 18 8 3",0),"null output");
    memset(&p,0,sizeof p);
    p.fd=5;p.level=1;p.class=FIGHTER;p.experience=350;
    p.strength=18;p.dexterity=18;p.constitution=18;
    p.intelligence=8;p.piety=3;
    hd74_progress(&p,0);
    ck(strstr(transcript,"Proposed XP for level 2: 1050 | Missing: 700")!=NULL,"real native struct preview threshold");
    ck(strstr(transcript,"NOT ACTIVE")!=NULL,"explicit no gameplay effect");
    ck(strstr(transcript,"up to 65 total stat points")!=NULL,"matching creation cap preview");
    memset(transcript,0,sizeof transcript);
    p.level=60;p.experience=400000;
    hd74_progress(&p,0);
    ck(strstr(transcript,"no next-level threshold")!=NULL,"cap preview");
    memset(transcript,0,sizeof transcript);
    p.level=-1;
    hd74_progress(&p,0);
    ck(strstr(transcript,"unavailable")!=NULL,"invalid level rejected");
    for(i=0;i<10;i++) ok("18 18 18 8 3",1);
    puts("ROUND 74B: strict native starting stats + real-creature progression preview PASS");
    return 0;
}
