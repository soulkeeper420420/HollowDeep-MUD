#define _GNU_SOURCE
#include "hd_player_store.h"
#include "atomic_player_snapshot.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <limits.h>
#include <sys/wait.h>

extern int hd_compress_bounded(char *,char *,int,int);
extern int write_crt_to_mem(char *,creature *,int);
extern int save_ply(), load_ply();
#ifdef HD_TEST_FILES2_WRAPPER
#define test_save(name,ptr) save_ply(name,ptr)
#define test_load(name,out) load_ply(name,out)
#else
#define test_save(name,ptr) hd_store_save_player(name,ptr)
#define test_load(name,out) hd_store_load_player(name,out)
#endif

int count_obj(object *obj, int perm_only) {
    otag *p; int count=0; (void)perm_only;
    for(p=obj->first_obj;p;p=p->next_tag)++count;
    return count;
}
int count_inv(creature *crt, int perm_only) {
    otag *p; int count=0; (void)perm_only;
    for(p=crt->first_obj;p;p=p->next_tag)++count;
    return count;
}
void merror(char *reason, int level) {
    fprintf(stderr,"Unexpected old native error: %s (%d)\n",reason,level);
    abort();
}
static void clear_items(otag *tag) {
    while(tag) {otag *next=tag->next_tag;
        if(tag->obj) {clear_items(tag->obj->first_obj);free(tag->obj);}
        free(tag);tag=next;}
}
static creature *make_player(long gold, int with_new) {
    creature *p=calloc(1,sizeof *p);
    otag *t=calloc(1,sizeof *t),*c=calloc(1,sizeof *c);
    object *a=calloc(1,sizeof *a),*b=calloc(1,sizeof *b);
    assert(p&&t&&c&&a&&b);
    strcpy(p->name,"Nativeqa");p->gold=gold;
    strcpy(a->name,"Round73 Chestplate");
    strcpy(b->name,"Existing Nested Token");
    p->first_obj=t;t->obj=a;a->first_obj=c;c->obj=b;
    if(with_new){
        otag *next=calloc(1,sizeof *next);
        object *item=calloc(1,sizeof *item);
        assert(next&&item);
        strcpy(item->name,"Round73 Reward Blade");
        next->obj=item;t->next_tag=next;
    }
    return p;
}
static void free_player(creature *p){
    if(p){clear_items(p->first_obj);free(p);}
}
static void verify_disk(long gold, int grant) {
    creature *loaded=NULL;
    assert(test_load("Nativeqa", &loaded)==0);
    assert(loaded&&loaded->gold==gold);
    assert(loaded->first_obj && loaded->first_obj->obj);
    assert(!strcmp(loaded->first_obj->obj->name,"Round73 Chestplate"));
    assert(loaded->first_obj->obj->first_obj);
    assert(!strcmp(loaded->first_obj->obj->first_obj->obj->name,
                  "Existing Nested Token"));
    assert(!!loaded->first_obj->next_tag == !!grant);
    if(grant) assert(!strcmp(loaded->first_obj->next_tag->obj->name,
                            "Round73 Reward Blade"));
    free_player(loaded);
}
int main(void) {
    char dir[]="/tmp/hd-round73g-save-XXXXXX";
    char claim[33], digest[65];
    creature *legacy, *reward, *again;
    int result;
    assert(mkdtemp(dir)); assert(chdir(dir)==0);assert(mkdir("player",0700)==0);
    memset(claim,'a',32);claim[32]=0;
    memset(digest,'f',64);digest[64]=0;
    legacy=make_player(30,0);reward=make_player(180,1);
    assert(test_save("Nativeqa",legacy)==HD_STORE_OK);
    verify_disk(30,0);
    assert(hd_store_read_claim("Nativeqa",claim,digest)==0);
    assert(hd_store_save_claim("Nativeqa",reward,claim,digest)==HD_STORE_OK);
    verify_disk(180,1);
    assert(hd_store_read_claim("Nativeqa",claim,digest)==1);
    again=make_player(1900,1);
    assert(hd_store_save_claim("Nativeqa",again,claim,digest)==HD_STORE_ALREADY_CLAIMED);
    verify_disk(180,1);
    /* Ordinary saves must carry the receipt forward with no caller sidecar. */
    assert(test_save("Nativeqa",reward)==HD_STORE_OK);
    assert(hd_store_read_claim("Nativeqa",claim,digest)==1);
    /* Fault before rename: old complete save persists. */
    assert(setenv("HD_ATOMIC_FAIL","before_rename",1)==0);
    assert(hd_store_save_player("Nativeqa",again)==HD_STORE_FAILURE);
    verify_disk(180,1);
    assert(unsetenv("HD_ATOMIC_FAIL")==0);
    /* Fault after rename: NEVER blindly retry; independently read receipt. */
    assert(setenv("HD_ATOMIC_FAIL","after_rename",1)==0);
    result=hd_store_save_player("Nativeqa",again);
    assert(result==HD_STORE_UNCERTAIN);
    assert(unsetenv("HD_ATOMIC_FAIL")==0);
    verify_disk(1900,1);
    assert(hd_store_read_claim("Nativeqa",claim,digest)==1);
    /* Cyclic tag/object graph is rejected before invoking legacy writer. */
    legacy->first_obj->obj->first_obj->next_tag=legacy->first_obj;
    assert(hd_store_save_player("Nativeqa",legacy)==HD_STORE_FAILURE);
    legacy->first_obj->obj->first_obj->next_tag=NULL;
    verify_disk(1900,1);
    /* Symlink target is never followed or replaced. */
    assert(rename("player/Nativeqa","player/OldSave")==0);
    assert(symlink("OldSave","player/Nativeqa")==0);
    assert(hd_store_save_player("Nativeqa",legacy)==HD_STORE_FAILURE);
    assert(unlink("player/Nativeqa")==0);
    assert(rename("player/OldSave","player/Nativeqa")==0);
    verify_disk(1900,1);
    /* Valid compression carrying a corrupt native count must not be parsed. */
    {
        unsigned char raw[20000], packed[10000];
        int rawlen, size, invalid_count=INT_MAX;
        assert(rename("player/Nativeqa","player/Backup") == 0);
        rawlen=write_crt_to_mem((char*)raw,reward,0);
        assert(rawlen > (int)sizeof(creature));
        memcpy(raw+sizeof(creature),&invalid_count,sizeof invalid_count);
        size=hd_compress_bounded((char*)raw,(char*)packed,rawlen,sizeof packed);
        assert(size>0);
        assert(hd_atomic_player_snapshot("player","Nativeqa",packed,size)==0);
        {
            creature *loaded=NULL;
            assert(test_load("Nativeqa",&loaded)==HD_STORE_FAILURE);
            assert(loaded==NULL);
        }
        assert(hd_store_save_player("Nativeqa",reward)==HD_STORE_FAILURE);
        assert(unlink("player/Nativeqa")==0);
        assert(rename("player/Backup","player/Nativeqa")==0);
        verify_disk(1900,1);
        /* Truncated receipt and arbitrary unknown trailers fail closed. */
        {
            hd_receipt_set set;
            size_t total;
            memset(&set,0,sizeof set);
            assert(hd_receipt_add(&set,claim,digest)==0);
            assert(hd_receipt_encode(raw,sizeof raw,rawlen,&set,&total)==0);
            raw[rawlen+6] ^= 1U; /* CRC mismatch */
            size=hd_compress_bounded((char*)raw,(char*)packed,(int)total,sizeof packed);
            assert(size>0);
            assert(rename("player/Nativeqa","player/Backup")==0);
            assert(hd_atomic_player_snapshot("player","Nativeqa",packed,size)==0);
            assert(hd_store_read_claim("Nativeqa",claim,digest)==-1);
            assert(hd_store_save_player("Nativeqa",reward)==HD_STORE_FAILURE);
            assert(unlink("player/Nativeqa")==0);
            assert(rename("player/Backup","player/Nativeqa")==0);
        }
        verify_disk(1900,1);
    }
    /* Concurrent native grant submissions serialize on the player directory;
     * only one process may apply an identical new receipt. */
    {
        char second[33], second_digest[65];
        pid_t children[4];
        int k, successes=0, already=0, status;
        memset(second,'b',32);second[32]=0;
        memset(second_digest,'e',64);second_digest[64]=0;
        for(k=0;k<4;k++) {
            children[k]=fork();
            assert(children[k]>=0);
            if(children[k]==0) {
                int rc=hd_store_save_claim("Nativeqa",again,second,second_digest);
                _exit(rc==HD_STORE_OK ? 10 : rc==HD_STORE_ALREADY_CLAIMED ? 11 : 12);
            }
        }
        for(k=0;k<4;k++) {
            assert(waitpid(children[k],&status,0)==children[k]);
            assert(WIFEXITED(status));
            if(WEXITSTATUS(status)==10)++successes;
            else if(WEXITSTATUS(status)==11)++already;
            else assert(!"unexpected concurrent grant error");
        }
        assert(successes==1 && already==3);
        verify_disk(1900,1);
        assert(hd_store_read_claim("Nativeqa",second,second_digest)==1);
    }
    free_player(again);free_player(reward);free_player(legacy);
    assert(unlink("player/Nativeqa")==0);
    assert(rmdir("player")==0);
    assert(chdir("/")==0);assert(rmdir(dir)==0);
    puts("ROUND 73G: real native inventory/gold/receipt/save/reload/retry/fault PASS");
    return 0;
}
