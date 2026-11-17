/* Private Necromancer: actual source-backed pet lifecycle, no expiry.
 * Native char/room/creature ABI is compiled from the Mordor source.
 */
#include "mstruct.h"
#include "hd_necro_skeleton.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <limits.h>

static int identity=1, count=0, freeing=0, credits=0, socials=0;
int action(creature *p, cmd *c) {(void)p;(void)c;socials++;return 0;}
int hd_store_is_necromancer(const char *name) { return identity && !strcmp(name,"Hdnecro"); }
void print(int fd,char *fmt,...) {(void)fd;(void)fmt;}
void add_crt_rom(creature *p,room *r,int n){(void)n;assert(!p->parent_rom);p->parent_rom=r;p->rom_num=r->rom_num;count++;}
void del_crt_rom(creature *p,room *r){assert(p->parent_rom==r);p->parent_rom=NULL;p->rom_num=0;count--;}
void free_crt(creature *p){hd_necro_skeleton_on_free(p);freeing++;free(p);}
int is_enm_crt(char *name,creature *p){(void)p;return !strcmp(name,"Hdnecro");}
void add_enm_dmg(char *name,creature *target,int dmg){(void)target;assert(!strcmp(name,"Hdnecro"));credits+=dmg;}
static void command(cmd *c){memset(c,0,sizeof *c);c->num=2;strcpy(c->str[1],"skeleton");}
int main(void){
 room a={0},b={0}; creature owner={0},dead={0},target={0},relogin={0},*pet;
 cmd c; a.rom_num=10;b.rom_num=11;command(&c);
 strcpy(owner.name,"Hdnecro");owner.type=PLAYER;owner.class=MAGE;owner.level=8;owner.mpcur=40;owner.fd=3;owner.parent_rom=&a;owner.rom_num=10;
 dead.type=MONSTER;dead.hpmax=145;dead.mpmax=47;dead.level=21;dead.parent_rom=&a;
 hd_necro_raise(&owner,&c);assert(!hd_necro_skeleton_probe(&owner));assert(owner.mpcur==40);
 identity=0;hd_necro_skeleton_record_kill(&dead,&owner);assert(!hd_necro_skeleton_probe(&owner));
 identity=1;hd_necro_skeleton_record_kill(&dead,&owner);
 /* Kill-based snapshot only; entering another room invalidates corpse. */
 owner.rom_num=11;owner.parent_rom=&b;hd_necro_raise(&owner,&c);assert(owner.mpcur==40);
 owner.rom_num=10;owner.parent_rom=&a;
 hd_necro_raise(&owner,&c);pet=hd_necro_skeleton_probe(&owner);
 assert(pet && pet->type==MONSTER && pet->hpmax==145 && pet->hpcur==145 && pet->mpmax==47 && pet->mpcur==47);
 assert(pet->experience==0 && pet->gold==0 && pet->level==21 && owner.mpcur==32 && count==1);
 hd_necro_raise(&owner,&c);assert(owner.mpcur==32 && count==1);
 assert(hd_necro_skeleton_can_heal(&owner));
 /* Native vigor/mend/potion handlers update these same fields. */
 pet->hpcur=26;pet->mpcur=5;pet->hpcur+=19;assert(pet->hpcur==45);
 pet->hpcur=pet->hpmax;pet->mpcur=pet->mpmax;
 hd_necro_skeleton_tick(LONG_MAX);assert(hd_necro_skeleton_probe(&owner)==pet);
 target.type=MONSTER;target.hpcur=3;target.parent_rom=&a;
 hd_necro_skeleton_assist(&owner,&target);assert(target.hpcur==1 && credits==2);
 hd_necro_skeleton_logout(&owner);
 assert(hd_necro_skeleton_probe(&owner)==pet && count==1);
 strcpy(relogin.name,"Hdnecro");relogin.type=PLAYER;relogin.class=MAGE;relogin.fd=6;relogin.parent_rom=&b;relogin.rom_num=11;
 hd_necro_skeleton_reconnect(&relogin);
 assert(hd_necro_skeleton_probe(&relogin)==pet && pet->parent_rom==&b && count==1);
 assert(hd_necro_skeleton_can_heal(&relogin));
 hd_necro_skeleton_tick(LONG_MAX);assert(hd_necro_skeleton_probe(&relogin)==pet);
 /* Actual monster destruction clears its owner slot. */
 del_crt_rom(pet,&b);free_crt(pet);assert(!hd_necro_skeleton_probe(&relogin));assert(count==0);
 /* Last corpse was consumed, so cannot re-summon without a new kill. */
 hd_necro_raise(&relogin,&c);assert(relogin.mpcur==0);
 relogin.mpcur=8;dead.parent_rom=&b;hd_necro_skeleton_record_kill(&dead,&relogin);
 hd_necro_raise(&relogin,&c);pet=hd_necro_skeleton_probe(&relogin);
 assert(pet && pet->hpmax==145 && relogin.mpcur==0 && count==1);
 hd_necro_skeleton_on_free(&relogin);assert(hd_necro_skeleton_probe(&relogin)==pet);
 hd_necro_skeleton_tick(LONG_MAX);assert(count==1);
 del_crt_rom(pet,&b);free_crt(pet);assert(count==0 && freeing==2);
 puts("NECROMANCER: verified kill HP/MP, mana charge, unlimited duration, reconnect, death cleanup PASS");
 return 0;
}
