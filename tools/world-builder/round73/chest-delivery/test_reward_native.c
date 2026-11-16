#define _GNU_SOURCE
/* Isolated native 73J chest -> kernel-verified daemon -> manifest ->
 * hd_native_reward_apply -> independently probed receipt -> ledger ACK.
 * This is a PRIVATE TEST HARNESS, not an engine command or release patch.
 */
#include "hd_guard_proof.h"
#include "hd_ledger_bridge.h"
#include "hd_native_reward.h"
#include "hd_reward_transport.h"
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static char message[512];
static int openexit_calls;
static int uncertain;
int openexit(creature *p,cmd *c){(void)p;(void)c;++openexit_calls;return 0;}
int hd_treasure_has_map(creature *p,const char *id) {
    /* Test stub ONLY. A production minted-map identity is NOT implemented. */
    return p && !strcmp(id,"map.0001") && !strcmp(p->name,"Nativeqa");
}
void print(int fd,char *fmt,...) {
    va_list ap;(void)fd;va_start(ap,fmt);
    vsnprintf(message,sizeof message,fmt,ap);va_end(ap);
}
int count_obj(object *o,int perm_only){
    otag *t;int n=0;(void)perm_only;
    for(t=o->first_obj;t;t=t->next_tag)++n;return n>80?80:n;
}
int count_inv(creature *p,int perm_only){
    otag *t;int n=0;(void)perm_only;
    for(t=p->first_obj;t;t=t->next_tag)++n;return n>80?80:n;
}
void merror(char *reason,int level){fprintf(stderr,"merror:%s %d\n",reason,level);abort();}
static int template_loader(int id,object **out,void *ctx) {
    object *o;(void)ctx;
    if(id!=123 && id!=124)return -1;
    o=(object *)calloc(1,sizeof *o);if(!o)return -1;
    strcpy(o->name,id==123?"Round73 Treasure Blade":"Round73 Rare Material");
    o->weight=2;
    *out=o;return 0;
}
static int can_carry(const creature *p,const object *obj,void *ctx) {
    (void)p;(void)ctx;return obj && obj->weight>=0 && obj->weight<=10;
}
extern int hd_treasure_open(creature *,cmd *);
extern void hd_treasure_guardian_death(creature *,creature *);
extern void hd_guard_evidence_test_restart(void);
int hd_claim_test_deliver(creature *p,const hd_guard_proof *proof) {
    hd_native_reward reward;
    const char *sock=getenv("HD_LEDGER_BRIDGE_TEST_SOCKET");
    int got, result;
    if(!sock)return -1;
    got=hd_reward_fetch(sock,HD_LEDGER_TRUSTED_UID,proof,&reward);
    if(got==HD_TRANSPORT_ALREADY)return 1;
    if(got!=HD_TRANSPORT_MANIFEST)return -1;
    /* Client does not choose gold, IDs or templates: all arrived from peer
     * with verified Unix socket credentials and are native-bounds validated. */
    if(getenv("HD_J_PREACK"))assert(hd_reward_ack(sock,HD_LEDGER_TRUSTED_UID,proof,&reward)==HD_TRANSPORT_DENIED);
    if(getenv("HD_J_FAULT"))setenv("HD_ATOMIC_FAIL",getenv("HD_J_FAULT"),1);
    result=hd_native_reward_apply(p,&reward,template_loader,can_carry,NULL);
    unsetenv("HD_ATOMIC_FAIL");
    if(result==HD_REWARD_UNCERTAIN) {uncertain=1;return -2;}
    if(result==HD_REWARD_DENIED)return -1;
    if(getenv("HD_J_SKIP_ACK"))return 2;
    if(hd_reward_ack(sock,HD_LEDGER_TRUSTED_UID,proof,&reward))return 2;
    return result==HD_REWARD_ALREADY?1:0;
}
static void free_tags(otag *t) {
    while(t){otag *next=t->next_tag;free_tags(t->obj->first_obj);free(t->obj);free(t);t=next;}
}
static void cleanup(creature *p){if(p){free_tags(p->first_obj);free(p);}}
static creature *new_player(void) {
    creature *p=(creature *)calloc(1,sizeof *p);
    otag *t=(otag *)calloc(1,sizeof *t);
    object *o=(object *)calloc(1,sizeof *o);
    otag *child=(otag *)calloc(1,sizeof *child);
    object *nested=(object *)calloc(1,sizeof *nested);
    assert(p&&t&&o&&child&&nested);
    strcpy(p->name,"Nativeqa");p->gold=30;p->type=PLAYER;p->rom_num=10001;
    strcpy(o->name,"Original Chestplate");strcpy(nested->name,"Nested Token");
    t->obj=o;p->first_obj=t;o->parent_crt=p;
    o->first_obj=child;child->obj=nested;nested->parent_obj=o;
    return p;
}
static void assert_inventory(const creature *p,int expected,long gold) {
    const otag *t;int n=0,old=0,blade=0,mat=0;
    assert(p->gold==gold);
    for(t=p->first_obj;t;t=t->next_tag) {
        ++n;
        if(!strcmp(t->obj->name,"Original Chestplate")) {
            assert(t->obj->first_obj);
            assert(!strcmp(t->obj->first_obj->obj->name,"Nested Token"));
            ++old;
        }
        if(!strcmp(t->obj->name,"Round73 Treasure Blade"))++blade;
        if(!strcmp(t->obj->name,"Round73 Rare Material"))++mat;
    }
    assert(n==expected && old==1 && (expected==1 || (blade==1&&mat==1)));
}
int main(int argc,char **argv) {
    room r;
    creature *owner,*on_disk,other,guard,decoy;
    ctag tag;
    cmd c;
    FILE *file;
    int mode,save_expected=1,initial_count;
    const char *mode_name=argc==3?argv[2]:"";
    if(argc!=3 || chdir(argv[1]))return 2;
    mode=!strcmp(mode_name,"initial")?0:!strcmp(mode_name,"replay")?1:-1;
    if(mode<0)return 2;
    memset(&r,0,sizeof r);r.rom_num=10001;
    memset(&other,0,sizeof other);strcpy(other.name,"Anotherqa");other.type=PLAYER;
    other.rom_num=10001;other.parent_rom=&r;
    memset(&guard,0,sizeof guard);strcpy(guard.name,"Native Guardian");
    guard.type=MONSTER;guard.rom_num=10001;
    memset(&decoy,0,sizeof decoy);strcpy(decoy.name,"Native Guardian");
    decoy.type=MONSTER;decoy.rom_num=10001;
    memset(&tag,0,sizeof tag);tag.crt=&guard;
    if(mode==0) {
        assert(mkdir("rooms",0700)==0);
        assert(mkdir("player",0700)==0);
        assert(mkdir("hollowdeep-data",0700)==0);
        assert(mkdir("hollowdeep-data/treasure-proof",0700)==0);
        file=fopen("rooms/treasure_guardians.map","w");assert(file);
        assert(fputs("HDGUARD1\n10001\tmap.0001\tNative Guardian\n",file)>0);
        assert(fclose(file)==0);
        owner=new_player();
        assert(hd_store_save_player("Nativeqa",owner)==HD_STORE_OK);
        r.first_mon=&tag;
    }else {
        assert(hd_store_load_player("Nativeqa",&owner)==0);
        initial_count=owner->gold==30?1:3;
        assert_inventory(owner,initial_count,owner->gold);
        r.first_mon=NULL;
    }
    owner->parent_rom=&r;owner->rom_num=10001;
    memset(&c,0,sizeof c);c.num=2;strcpy(c.str[1],"chest");
    if(mode==0) {
        assert(hd_treasure_open(owner,&c)==0 && strstr(message,"locked"));
        hd_treasure_guardian_death(&decoy,owner);
        hd_treasure_guardian_death(&guard,&other);
        hd_guard_evidence_test_restart();
        assert(hd_treasure_open(owner,&c)==0 && strstr(message,"locked"));
        hd_treasure_guardian_death(&guard,owner);
    }
    assert(hd_treasure_open(owner,&c)==0);
    if(mode==0) {
        if(getenv("HD_J_FAULT") && !strcmp(getenv("HD_J_FAULT"),"before_rename")) {
            assert(strstr(message,"denied") && !uncertain);
            assert_inventory(owner,1,30);
        }else if(getenv("HD_J_FAULT") && !strcmp(getenv("HD_J_FAULT"),"after_rename")) {
            assert(strstr(message,"uncertain") && uncertain);
            assert_inventory(owner,1,30);
            save_expected=3;
        }else {
            assert(strstr(message,"securely saved") || strstr(message,"acknowledgment pending"));
            assert_inventory(owner,3,180);
            save_expected=3;
        }
        assert(hd_store_load_player("Nativeqa",&on_disk)==0);
        assert_inventory(on_disk,save_expected,save_expected==3?180:30);
        cleanup(on_disk);
    }else {
        assert(strstr(message,"already claimed") || strstr(message,"acknowledgment pending") || strstr(message,"securely saved"));
        assert_inventory(owner,3,180);
    }
    memset(&c,0,sizeof c);c.num=2;strcpy(c.str[1],"door");
    assert(hd_treasure_open(owner,&c)==0 && openexit_calls==1);
    if(uncertain) {
        /* Simulated session terminates. DO NOT save stale live state. */
        puts("ROUND 73J: uncertain save blocks session until reload PASS");
    }
    cleanup(owner);
    puts(mode==0?"ROUND 73J: native chest grant/save/receipt gameplay PASS":
                 "ROUND 73J: native chest reconnect/no duplicate claim PASS");
    return 0;
}
