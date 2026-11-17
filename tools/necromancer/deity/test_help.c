/* Exercise the actual native help dispatcher using isolated help files. */
#include "mstruct.h"
#include "hollowdeep_help.h"
#include "hollowdeep_staff.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
static int role=HD_ROLE_ADMIN;
static char opened[160], output[16384];
static int pages;
struct { char *cmdstr; int cmdno; int (*cmdfn)(); } cmdlist[] = {
 {"raise",100,0},{"raiseskeleton",150,0},{"*deity",151,0},{"help",14,0},{0,0,0}};
struct { char *splstr; int splno; int (*splfn)(); } spllist[] = {{0,-1,0}};
void print(int fd,const char *fmt,...) { va_list ap;size_t n=strlen(output); (void)fd;va_start(ap,fmt);vsnprintf(output+n,sizeof output-n,fmt,ap);va_end(ap); }
void view_file(int fd,int param,char *path) { FILE *f;char b[64];(void)fd;(void)param;f=fopen(path,"r");assert(f);assert(fgets(b,sizeof b,f));fclose(f);assert(strlen(path)<sizeof opened);strcpy(opened,path);pages++; }
int hd_staff_role(creature *p){(void)p;return role;}
int hd_staff_rank(int r){return r==HD_ROLE_OWNER?3:r==HD_ROLE_ADMIN?2:r==HD_ROLE_MOD?1:r==HD_ROLE_PLAYER?0:-1;}
const char *hd_staff_badge(creature *p){(void)p;return "[staff]";}
int hd_build_access(creature *p,int r){(void)p;(void)r;return 0;}
int hd_store_is_necromancer(const char *n){return !strcmp(n,"Hdnecro");}
static void parse(cmd *c,const char *s){memset(c,0,sizeof *c);strcpy(c->fullstr,s);opened[0]=output[0]=0;}
static void page(creature *p,const char *s,const char *expected) {cmd c;parse(&c,s);help(p,&c);assert(!strcmp(opened,expected));}
int main(void){creature p={0};cmd c; p.type=PLAYER;p.class=MAGE;p.level=1;p.fd=4;strcpy(p.name,"Hdnecro");
 page(&p,"help necromancer","help/necromancer");page(&p,"help raise skeleton","help/help.150");page(&p,"help raiseskeleton","help/help.150");page(&p,"help deity","help/deity");page(&p,"help corpse","help/corpses-pending");page(&p,"help sacrifice corpse","help/corpses-pending");page(&p,"help raise corpse","help/corpses-pending");
 page(&p,"help *deity","");assert(!hd_native_command_allowed(&p,151));p.class=DM;role=HD_ROLE_MOD;page(&p,"help *deity","");assert(!hd_native_command_allowed(&p,151));role=HD_ROLE_ADMIN;page(&p,"help *deity","help/help.151");assert(hd_native_command_allowed(&p,151));parse(&c,"dmcommands");dmcommands(&p,&c);assert(strstr(output,"*deity <player>"));p.class=MAGE;parse(&c,"skills");skills(&p,&c);assert(strstr(output,"raise skeleton [eligible]"));strcpy(p.name,"Hdmage");parse(&c,"skills");skills(&p,&c);assert(!strstr(output,"raise skeleton"));parse(&c,"skills all");skills(&p,&c);assert(strstr(output,"raise skeleton [Necromancer]"));assert(pages==8);puts("DEITY: native help routing, real page files, unique command IDs, staff visibility and Necromancer skill listing PASS");return 0;}
