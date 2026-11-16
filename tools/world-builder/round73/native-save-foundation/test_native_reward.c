/* Fully disposable test: native inventory, receipt, atomic save/reload.
 * Uses the actual Mordor files2/files3 serializers from the private stage.
 */
#define _GNU_SOURCE
#include "hd_native_reward.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef HD_LEDGER_FIXTURE
#include "hd_generated_manifest.h"
#endif

int count_obj(object *obj, int perm_only) {
    const otag *t; int c=0; (void)perm_only;
    for (t=obj->first_obj; t; t=t->next_tag) ++c;
    return c;
}
int count_inv(creature *p, int perm_only) {
    const otag *t; int c=0; (void)perm_only;
    for (t=p->first_obj; t; t=t->next_tag) ++c;
    return c > 80 ? 80:c;
}
void merror(char *reason, int level) {
    fprintf(stderr,"Unexpected native error: %s %d\n",reason,level);
    abort();
}
static int allow_template(int id, object **out, void *ctx) {
    object *o; (void)ctx;
    if (id!=123 && id!=124) return -1;
    o=(object *)calloc(1,sizeof *o);
    assert(o);
    strcpy(o->name,id==123 ? "Round73 Treasure Blade" : "Round73 Rare Material");
    o->weight=2;
    *out=o;
    return 0;
}
static int can_carry(const creature *player, const object *o,void *ctx) {
    (void)player;(void)ctx;
    return o->weight<=10;
}
static void free_chain(otag *t) {
    while(t) {
        otag *next=t->next_tag;
        free_chain(t->obj->first_obj);
        free(t->obj); free(t); t=next;
    }
}
static creature *make_player(void) {
    creature *p=(creature *)calloc(1,sizeof *p);
    otag *t=(otag *)calloc(1,sizeof *t);
    object *obj=(object *)calloc(1,sizeof *obj);
    otag *nested=(otag *)calloc(1,sizeof *nested);
    object *token=(object *)calloc(1,sizeof *token);
    assert(p&&t&&obj&&nested&&token);
    strcpy(p->name,"Nativeqa");p->gold=30;
    strcpy(obj->name,"Original Chestplate");
    strcpy(token->name,"Nested Token");
    p->first_obj=t;t->obj=obj;t->obj->parent_crt=p;
    obj->first_obj=nested;nested->obj=token;token->parent_obj=obj;
    return p;
}
static void destroy(creature *p) {if(p){free_chain(p->first_obj);free(p);}}
static void fill_hex(char *buf,int n,char letter){memset(buf,letter,n);buf[n]=0;}
static hd_native_reward good_manifest(void) {
    hd_native_reward m;
    memset(&m,0,sizeof m);
    strcpy(m.owner,"Nativeqa");
    fill_hex(m.claim_id,32,'a');fill_hex(m.digest,64,'f');
    m.count=2;m.gold=150;
    fill_hex(m.items[0].instance_id,32,'b');
    fill_hex(m.items[1].instance_id,32,'c');
#ifdef HD_LEDGER_FIXTURE
    /* Genuine Python claim ledger + immutable reward manifest snapshot. */
    strcpy(m.claim_id,HD_FIX_CLAIM_ID);
    strcpy(m.digest,HD_FIX_DIGEST);
    strcpy(m.items[0].instance_id,HD_FIX_ITEM0);
    strcpy(m.items[1].instance_id,HD_FIX_ITEM1);
#endif
    m.items[0].kind='i';m.items[0].template_id=123;
    m.items[1].kind='m';m.items[1].template_id=124;
    return m;
}
static void disk_expected(int count,long gold,const hd_native_reward *m) {
    creature *p=NULL;
    otag *tag;
    int n=0;
    assert(hd_store_load_player("Nativeqa",&p)==0);
    assert(p&&p->gold==gold);
    for(tag=p->first_obj;tag;tag=tag->next_tag)++n;
    assert(n==count);
    if(m) assert(hd_store_read_claim("Nativeqa",m->claim_id,m->digest)==1);
    /* The preserved nested original inventory remains accessible. */
    for(tag=p->first_obj;tag;tag=tag->next_tag) {
        if(!strcmp(tag->obj->name,"Original Chestplate")) {
            assert(tag->obj->first_obj);
            assert(!strcmp(tag->obj->first_obj->obj->name,"Nested Token"));
            destroy(p);return;
        }
    }
    assert(!"Original inventory lost");
}
int main(void) {
    char temp[]="/tmp/hollowdeep-73g-grant-XXXXXX";
    creature *live,*reload;
    hd_native_reward m,m2,bad;
    int rc;
    assert(mkdtemp(temp));assert(chdir(temp)==0);
    assert(mkdir("player",0700)==0);
    live=make_player();assert(hd_store_save_player("Nativeqa",live)==0);
    m=good_manifest();
    /* Denied attempts cause neither memory nor disk mutation. */
    bad=m;strcpy(bad.owner,"Otherqa");
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    bad=m;bad.items[1].template_id=OMAX;
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    bad=m;bad.items[0].enchant_power=3;
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    bad=m;strcpy(bad.items[1].instance_id,bad.items[0].instance_id);
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    bad=m;bad.items[1].template_id=125; /* Unknown native template. */
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    bad=m;bad.gold=1000001L; /* Ledger total gold cap. */
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    disk_expected(1,30,NULL);
    assert(hd_native_reward_apply(live,&m,allow_template,can_carry,NULL)==HD_REWARD_APPLIED);
    assert(live->gold==180&&live->first_obj->obj->parent_crt==live);
    disk_expected(3,180,&m);
    assert(hd_native_reward_apply(live,&m,allow_template,can_carry,NULL)==HD_REWARD_ALREADY);
    disk_expected(3,180,&m);
    bad=m;bad.digest[0]='0'; /* Exact claim key with different receipt. */
    assert(hd_native_reward_apply(live,&bad,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    /* Relaunch/load after commit: the receipt prevents duplicates. */
    assert(hd_store_load_player("Nativeqa",&reload)==0);
    assert(hd_native_reward_apply(reload,&m,allow_template,can_carry,NULL)==HD_REWARD_ALREADY);
    destroy(reload);
    m2=m;fill_hex(m2.claim_id,32,'d');fill_hex(m2.digest,64,'e');
    fill_hex(m2.items[0].instance_id,32,'1');fill_hex(m2.items[1].instance_id,32,'2');
    assert(setenv("HD_ATOMIC_FAIL","before_rename",1)==0);
    assert(hd_native_reward_apply(live,&m2,allow_template,can_carry,NULL)==HD_REWARD_DENIED);
    assert(live->gold==180);
    assert(unsetenv("HD_ATOMIC_FAIL")==0);
    disk_expected(3,180,&m);
    assert(setenv("HD_ATOMIC_FAIL","after_rename",1)==0);
    rc=hd_native_reward_apply(live,&m2,allow_template,can_carry,NULL);
    assert(unsetenv("HD_ATOMIC_FAIL")==0);
    assert(rc==HD_REWARD_UNCERTAIN);
    /* Visible receipt after an interrupted post-rename fsync does not mean
     * durable. Caller must block the original live session from saving. */
    assert(live->gold==180);
    disk_expected(5,330,&m2);
    assert(hd_store_load_player("Nativeqa",&reload)==0);
    assert(reload->gold==330);
    assert(hd_native_reward_apply(reload,&m2,allow_template,can_carry,NULL)==HD_REWARD_ALREADY);
    /* Legitimate gold-only grant on a newly loaded session. */
    {
        hd_native_reward gold_only=m;
        fill_hex(gold_only.claim_id,32,'7');
        fill_hex(gold_only.digest,64,'8');
        gold_only.count=0;gold_only.gold=17;
        assert(hd_native_reward_apply(reload,&gold_only,allow_template,can_carry,NULL)==HD_REWARD_APPLIED);
        disk_expected(5,347,&gold_only);
        assert(hd_store_read_claim("Nativeqa",m.claim_id,m.digest)==1);
        assert(hd_store_read_claim("Nativeqa",m2.claim_id,m2.digest)==1);
        assert(hd_native_reward_apply(reload,&gold_only,allow_template,can_carry,NULL)==HD_REWARD_ALREADY);
    }
    destroy(reload);
    destroy(live);
    assert(unlink("player/Nativeqa")==0);
    assert(rmdir("player")==0);
    assert(chdir("/")==0);assert(rmdir(temp)==0);
    puts("ROUND 73G: trusted native reward staging/rollback/receipt/restart PASS");
    return 0;
}
