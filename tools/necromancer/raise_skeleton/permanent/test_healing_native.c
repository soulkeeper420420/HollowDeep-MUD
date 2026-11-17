/* Execute native vigor/mend/restore and drink() against a real skeleton.
 * All fixtures are disposable; no game listener or player files.
 */
#include "mstruct.h"
#include "hd_necro_skeleton.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>

int bonus[100];
static room r;
static creature owner;
static object potion;
static int count=0;
static ctag mon_tag;
extern int vigor(creature *, cmd *, int);
extern int mend(creature *, cmd *, int);
extern int restore(creature *, cmd *, int);
extern int drink(creature *, cmd *);
struct {int splno;char realm;int mp;int ndice;int sdice;int pdice;char bonus_type;} ospell[]={{-1,0,0,0,0,0,0}};
int mprofic(creature *p,int x){(void)p;(void)x;return 0;}
int is_charm_crt(char *name,creature *p){(void)name;(void)p;return 0;}
int add_enm_crt(char *name,creature *p){(void)name;(void)p;return 0;}
void die(creature *p,creature *k){(void)p;(void)k;}
extern int offensive_spell();
struct {char *splstr;int splno;int (*splfn)();} spllist[] = {
 {"vigor", SVIGOR, (int (*)())vigor},
 {"mend-wounds", SMENDW, (int (*)())mend},
 {"restore", SRESTO, (int (*)())restore},
 {"end", -1, 0}
};
int hd_store_is_necromancer(const char *n){return !strcmp(n,"Hdnecro");}
void print(int fd,char *fmt,...){(void)fmt;assert(fd>=0);}
void broadcast_rom(int fd,int rom,char *fmt,...){(void)fd;(void)rom;(void)fmt;}
void broadcast_rom2(int a,int b,int c,char *fmt,...){(void)a;(void)b;(void)c;(void)fmt;}
void add_crt_rom(creature *p,room *loc,int n){(void)n;assert(!p->parent_rom);p->parent_rom=loc;p->rom_num=loc->rom_num;mon_tag.crt=p;mon_tag.next_tag=NULL;loc->first_mon=&mon_tag;count++;}
void del_crt_rom(creature *p,room *loc){assert(p->parent_rom==loc);p->parent_rom=NULL;loc->first_mon=NULL;count--;}
void free_crt(creature *p){hd_necro_skeleton_on_free(p);free(p);}
int action(creature *p,cmd *c){(void)p;(void)c;return 0;}
int is_enm_crt(char *n,creature *p){(void)n;(void)p;return 1;}
void add_enm_dmg(char *n,creature *p,int d){(void)n;(void)p;(void)d;}
int spell_fail(creature *p,int how){(void)p;(void)how;return 0;}
int dice(int n,int s,int b){(void)s;return n*6+b;}
int up(int x){return toupper((unsigned char)x);}
int low(int x){return tolower((unsigned char)x);}
creature *find_crt(creature *healer,ctag *first,char *name,int val){
 (void)healer;(void)val;
 if(first==&mon_tag && mon_tag.crt && !strncmp(name,"skeleton",8))return mon_tag.crt;
 return NULL;
}
object *find_obj(creature *p,otag *obj,char *name,int index){
 (void)p;(void)obj;(void)index;
 return !strcmp(name,"potion")?&potion:NULL;
}
void del_obj_crt(object *o,creature *p){(void)o;(void)p;}
void free_obj(object *o){(void)o;}
void add_obj_rom(object *o,room *loc){(void)o;(void)loc;}
static void fill_cmd(cmd *c,int target){
 memset(c,0,sizeof *c);
 if(target){c->num=3;strcpy(c->str[2],"skeleton");c->val[2]=1;}
 else {c->num=4;strcpy(c->str[1],"potion");strcpy(c->str[2],"on");strcpy(c->str[3],"skeleton");c->val[1]=1;}
}
int main(void){
 creature dead={0},*pet;cmd c;
 memset(&r,0,sizeof r);r.rom_num=40;
 memset(&owner,0,sizeof owner);strcpy(owner.name,"Hdnecro");owner.type=PLAYER;owner.class=MAGE;
 owner.fd=7;owner.parent_rom=&r;owner.rom_num=40;owner.mpcur=24;owner.piety=10;owner.intelligence=10;
 dead.type=MONSTER;dead.parent_rom=&r;dead.hpmax=73;dead.mpmax=29;dead.level=12;
 hd_necro_skeleton_record_kill(&dead,&owner);
 memset(&c,0,sizeof c);c.num=2;strcpy(c.str[1],"skeleton");
 hd_necro_raise(&owner,&c);pet=hd_necro_skeleton_probe(&owner);
 assert(pet && pet->hpmax==73 && pet->mpmax==29 && count==1);
 pet->hpcur=25;fill_cmd(&c,1);
 assert(vigor(&owner,&c,WAND)==1 && pet->hpcur>25 && pet->hpcur<=73);
 pet->hpcur=10;fill_cmd(&c,1);
 assert(mend(&owner,&c,WAND)==1 && pet->hpcur>10 && pet->hpcur<=73);
 pet->hpcur=4;pet->mpcur=0;fill_cmd(&c,1);
 assert(restore(&owner,&c,WAND)==1 && pet->hpcur>4 && pet->hpcur<=73);
 /* Targeted healing potion reuses existing magic dispatch + charge/shot. */
 memset(&potion,0,sizeof potion);potion.type=POTION;potion.shotscur=2;potion.magicpower=1;
 pet->hpcur=9;fill_cmd(&c,0);drink(&owner,&c);
 assert(pet->hpcur>9 && pet->hpcur<=73 && potion.shotscur==1);
 potion.magicpower=3;pet->mpcur=0;pet->hpcur=12;fill_cmd(&c,0);drink(&owner,&c);
 assert(pet->hpcur>12 && pet->hpcur<=73 && potion.shotscur==0);
 /* Native hpcur/hpmax use signed short; healing must not wrap at 32767. */
 pet->hpmax=32767;pet->hpcur=32766;fill_cmd(&c,1);
 assert(vigor(&owner,&c,WAND)==1 && pet->hpcur==32767);
 pet->hpcur=32765;fill_cmd(&c,1);
 assert(mend(&owner,&c,WAND)==1 && pet->hpcur==32767);
 pet->hpcur=32766;fill_cmd(&c,1);
 assert(restore(&owner,&c,WAND)==1 && pet->hpcur==32767);
 del_crt_rom(pet,&r);free_crt(pet);
 assert(!hd_necro_skeleton_probe(&owner));
 puts("NECROMANCER: actual native Vigor/Mend/Restore + targeted healing potions PASS");
 return 0;
}
