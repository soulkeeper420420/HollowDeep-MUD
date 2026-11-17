/* Test real C pet lifecycle in isolated rooms without a game listener. */
#include "mstruct.h"
#include "hd_necro_skeleton.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static int identity=1, monster_count=0, frees=0, reports=0, credits=0, socials=0;
int action(creature *p, cmd *c) {(void)p;(void)c;socials++;return 0;}
int hd_store_is_necromancer(const char *name) { return identity && !strcmp(name, "Hdnecro"); }
void print(int fd, char *fmt, ...) { (void)fd;(void)fmt;reports++; }
void add_crt_rom(creature *p,room *r,int n) {(void)n;assert(!p->parent_rom);p->parent_rom=r;p->rom_num=r->rom_num;monster_count++;}
void del_crt_rom(creature *p,room *r){assert(p->parent_rom==r);p->parent_rom=NULL;p->rom_num=0;monster_count--;}
void free_crt(creature *p){hd_necro_skeleton_on_free(p);frees++;free(p);}
int is_enm_crt(char *name, creature *target){(void)target;return !strcmp(name,"Hdnecro");}
void add_enm_dmg(char *name, creature *target, int dmg){(void)target;assert(!strcmp(name,"Hdnecro"));credits+=dmg;}

static void init_cmd(cmd *c){memset(c,0,sizeof *c);c->num=2;strcpy(c->str[1],"skeleton");}
int main(void)
{
    creature owner={0},other={0},target={0},*pet;
    room a={0},b={0};cmd c;
    a.rom_num=10; b.rom_num=11;
    strcpy(owner.name,"Hdnecro"); owner.type=PLAYER; owner.class=MAGE;owner.level=8;owner.mpcur=35;owner.fd=3;owner.parent_rom=&a;
    init_cmd(&c);
    identity=0; hd_necro_raise(&owner,&c); assert(!hd_necro_skeleton_probe(&owner));
    identity=1;
    strcpy(c.str[1],"goblet");hd_necro_raise_or_action(&owner,&c);assert(socials==1);
    strcpy(c.str[1],"zombie");hd_necro_raise(&owner,&c); assert(!hd_necro_skeleton_probe(&owner));
    strcpy(c.str[1],"skeleton");
    hd_necro_raise_or_action(&owner,&c);pet=hd_necro_skeleton_probe(&owner);
    assert(pet && pet->type==MONSTER && pet->class==FIGHTER && pet->experience==0 && pet->gold==0);
    assert(monster_count==1 && owner.mpcur==27 && pet->parent_rom==&a);
    hd_necro_raise(&owner,&c);assert(monster_count==1 && owner.mpcur==27);
    owner.parent_rom=&b;hd_necro_skeleton_follow(&owner,&a,&b); assert(pet->parent_rom==&b && monster_count==1);
    target.type=MONSTER;target.hpcur=3;target.parent_rom=&b;
    hd_necro_skeleton_assist(&owner,&target);assert(target.hpcur==1 && credits==2);
    hd_necro_skeleton_assist(&owner,&target);assert(target.hpcur==1);
    strcpy(other.name,"Hdmage");other.type=PLAYER;other.class=MAGE;other.fd=4;other.parent_rom=&b;other.mpcur=50;
    hd_necro_raise(&other,&c);assert(!hd_necro_skeleton_probe(&other));
    hd_necro_skeleton_logout(&owner);assert(!hd_necro_skeleton_probe(&owner) && monster_count==0 && frees==1);
    owner.mpcur=20;hd_necro_raise(&owner,&c);pet=hd_necro_skeleton_probe(&owner);assert(pet);
    /* Deserialization/room cleanup may free pet without calling logout. */
    del_crt_rom(pet,&b);free_crt(pet);assert(!hd_necro_skeleton_probe(&owner));
    owner.mpcur=20;hd_necro_raise(&owner,&c);assert(hd_necro_skeleton_probe(&owner));
    hd_necro_skeleton_tick(2147483647L);assert(!hd_necro_skeleton_probe(&owner));
    assert(monster_count==0 && frees==3);
    puts("NECROMANCER: private Raise Skeleton owner, identity, spawn, follow, assist, lifetime, cleanup PASS");
    return 0;
}
