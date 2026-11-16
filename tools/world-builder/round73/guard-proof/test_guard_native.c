#define _GNU_SOURCE
#include "mstruct.h"
#include "hd_guard_proof.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static char last_message[512];
static int original_open_called;
int openexit(creature *p,cmd *c){(void)p;(void)c; ++original_open_called;return 0;}
int hd_treasure_has_map(creature *p,const char *id){
    return p && !strcmp(id,"map.0001");
}
void print(int fd,char *fmt,...) {
    va_list ap;
    (void)fd;
    va_start(ap,fmt);
    vsnprintf(last_message,sizeof last_message,fmt,ap);
    va_end(ap);
}
extern int hd_treasure_open(creature *,cmd *);
extern void hd_treasure_guardian_death(creature *,creature *);
extern void hd_guard_evidence_test_restart(void);
int main(void) {
    char tmp[]="/tmp/hollowdeep-73h-native-XXXXXX";
    room r;
    creature owner,other,guardian,decoy;
    ctag tag;
    cmd c;
    assert(mkdtemp(tmp) && chdir(tmp)==0);
    assert(mkdir("rooms",0700)==0);
    assert(mkdir("hollowdeep-data",0700)==0);
    assert(mkdir("hollowdeep-data/treasure-proof",0700)==0);
    {
        FILE *f=fopen("rooms/treasure_guardians.map","w");
        assert(f);
        assert(fputs("HDGUARD1\n10001\tmap.0001\tNative Guardian\n",f)>0);
        assert(fclose(f)==0);
    }
    memset(&r,0,sizeof r); r.rom_num=10001;
    memset(&owner,0,sizeof owner);
    strcpy(owner.name,"Nativeqa"); owner.type=PLAYER; owner.rom_num=10001;
    owner.parent_rom=&r;
    memset(&other,0,sizeof other);
    strcpy(other.name,"Anotherqa"); other.type=PLAYER; other.rom_num=10001;
    other.parent_rom=&r;
    memset(&guardian,0,sizeof guardian);
    strcpy(guardian.name,"Native Guardian");guardian.type=MONSTER;guardian.rom_num=10001;
    memset(&decoy,0,sizeof decoy);
    strcpy(decoy.name,"Native Guardian");decoy.type=MONSTER;decoy.rom_num=10001;
    memset(&tag,0,sizeof tag);tag.crt=&guardian;r.first_mon=&tag;
    memset(&c,0,sizeof c);c.num=2;strcpy(c.str[1],"chest");
    assert(hd_treasure_open(&owner,&c)==0);
    assert(strstr(last_message,"locked"));
    /* A template-identical monster pointer cannot be credited. */
    hd_treasure_guardian_death(&decoy,&owner);
    hd_guard_evidence_test_restart();
    assert(hd_treasure_open(&owner,&c)==0);
    assert(strstr(last_message,"locked"));
    hd_treasure_guardian_death(&guardian,&other);
    hd_guard_evidence_test_restart();
    assert(hd_treasure_open(&owner,&c)==0);
    assert(strstr(last_message,"locked"));
    hd_treasure_guardian_death(&guardian,&owner);
    assert(hd_treasure_open(&owner,&c)==0);
    assert(strstr(last_message,"seals dissolve"));
    assert(strstr(last_message,"reward delivery is disabled"));
    /* The same challenge remains cleared across a simulated restart. */
    hd_guard_evidence_test_restart();
    r.first_mon=NULL;
    assert(hd_treasure_open(&owner,&c)==0);
    assert(strstr(last_message,"reward delivery is disabled"));
    assert(hd_treasure_open(&other,&c)==0);
    assert(strstr(last_message,"Another") || strstr(last_message,"cannot"));
    /* Unrelated doors still route through original openexit. */
    memset(&c,0,sizeof c);c.num=2;strcpy(c.str[1],"door");
    assert(hd_treasure_open(&owner,&c)==0 && original_open_called==1);
    puts("ROUND 73H: native pointer-only death, restart recovery, owner denial, disabled rewards PASS");
    return 0;
}
