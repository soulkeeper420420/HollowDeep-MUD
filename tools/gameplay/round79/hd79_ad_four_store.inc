/* Round79AD R3: ONLY include at end of native hd_player_store.c AFTER
 * hd79_mount_presence_store.inc. Reuses verified PLAYERPATH lock, native
 * player format, receipt encoder, compression and atomic snapshot.
 * Old two/three-receipt mount writers are blocked by the staging feature.
 */
#if !defined(HD79_AD_FOUR_STORE_PLAYTEST) || \
    !defined(HD79_MOUNT_PRESENCE_STORE_PLAYTEST) || \
    !defined(HD79_BREATH_STORE_PLAYTEST)
#error "Four-way mount store requires verified atomic native presence + Breath"
#endif
#include "hd79_ad_four_store.h"
#include "hd79_ad_death_receipt.h"
#include "hd79_mount_ids.h"
#include "hd79_mount_wire.h"
#include <string.h>

/* Missing #83 with a POPULATED triple is never considered an empty roster. */
static int hd79_ad_four_snapshot(const hd_receipt_set *set,const char *epoch,
                                  hd79_mount_roster *r,
                                  hd79_mount_presence *p,
                                  hd79_ad_death_receipt *d)
{
    hd79_mount_roster state;
    hd79_mount_presence pos;
    hd79_ad_death_receipt tomb;
    int old,dead;
    if(!set||!epoch||!r||!p||!d)return -1;
    old=hd79_presence_snapshot(set,epoch,&state,&pos);
    dead=hd79_mount_find(set,HD79_AD_DEATH_RECEIPT_ID);
    if(old==1&&dead<0)return 1;
    if(old!=0||dead<0||
       hd79_ad_death_wire_decode(&state,
            set->entries[dead].manifest_sha256,&tomb))return -1;
    *r=state;*p=pos;*d=tomb;
    return 0;
}
int hd79_ad_four_store_read(const char *name,hd79_mount_roster *r,
                            hd79_mount_presence *p,
                            hd79_ad_death_receipt *d)
{
    unsigned char *raw=NULL;
    hd_receipt_set set;
    hd79_mount_roster a;
    hd79_mount_presence b;
    hd79_ad_death_receipt c;
    char epoch[25];
    size_t used=0,native=0;
    int rc,result=HD79_AD_FOUR_FAILURE;
    if(!valid_name(name)||!r||!p||!d)return result;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    if(!raw)return result;
    if(read_record(name,raw,&used,&native,&set)||
       ((creature *)raw)->type!=PLAYER||
       !native_name(((creature *)raw)->name,name)||
       hd79_mount_authoritative_epoch(&set,epoch))goto done;
    rc=hd79_ad_four_snapshot(&set,epoch,&a,&b,&c);
    if(rc==1)result=HD79_AD_FOUR_ABSENT;
    else if(rc==0){*r=a;*p=b;*d=c;result=HD79_AD_FOUR_OK;}
done:
    free(raw);
    return result;
}

/* Compare canonical wires, never C struct padding. Caller supplies only
 * prior state, not a player-derived name/room. Locked disk state wins. */
static int hd79_ad_four_matches(const hd_receipt_set *set,
                                 const hd79_mount_roster *r,
                                 const hd79_mount_presence *p,
                                 const hd79_ad_death_receipt *d)
{
    char a[65],b[65],c[65],e[65];
    int ia,ib,ic,id;
    if(!set||!r||!p||!d||
       hd79_mount_wire_encode(r,a,b)||
       hd79_presence_encode(r,p,c)||
       hd79_ad_death_wire_encode(r,d,e))return 0;
    ia=hd79_mount_find(set,hd79_mount_a_id);
    ib=hd79_mount_find(set,hd79_mount_b_id);
    ic=hd79_mount_find(set,HD79_MOUNT_PRESENCE_ID);
    id=hd79_mount_find(set,HD79_AD_DEATH_RECEIPT_ID);
    return ia>=0&&ib>=0&&ic>=0&&id>=0&&
      !strcmp(set->entries[ia].manifest_sha256,a)&&
      !strcmp(set->entries[ib].manifest_sha256,b)&&
      !strcmp(set->entries[ic].manifest_sha256,c)&&
      !strcmp(set->entries[id].manifest_sha256,e);
}

/* Shared locked operation for one-time initialize, monotone death, and a
 * compile-time TEST-ONLY fixture award. No generic untrusted state patch. */
static int hd79_ad_four_transaction(const char *name,unsigned mode,
                                     const hd79_mount_roster *expected,
                                     const hd79_mount_presence *oldp,
                                     const hd79_ad_death_receipt *oldd,
                                     unsigned id,int species,unsigned room_id,
                                     hd79_mount_roster *rout,
                                     hd79_mount_presence *pout,
                                     hd79_ad_death_receipt *dout)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set set;
    hd79_mount_roster r,nextr,prior;
    hd79_mount_presence p,nextp,priorp;
    hd79_ad_death_receipt d,nextd,priord;
    char epoch[25],wa[65],wb[65],wc[65],wd[65];
    size_t used=0,native=0,total=0;
    creature *disk;
    int lock=-1,a,b,c,e,prior_status,length,wr;
    int rc=HD79_AD_FOUR_FAILURE;
    unsigned awarded=0;
    if(!valid_name(name)||!dout||(mode!=2&&!rout)||(mode!=2&&!pout))
        return rc;
    if(mode!=0 && (!expected||!oldp||!oldd||
       !hd79_presence_valid(expected,oldp)||
       !hd79_ad_death_valid(expected,oldd)))return rc;
    if(mode==2 && (!id||id>expected->count))return rc;
    if(mode==3 && (!room_id||room_id>HD79_PRESENCE_MAX_ROOM))return rc;
    if(mode!=0&&mode!=2&&mode!=3)return rc;
    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if(!raw||!packed)goto done;
    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(lock<0||flock(lock,LOCK_EX)<0||
       read_record(name,raw,&used,&native,&set))goto done;
    disk=(creature *)raw;
    if(disk->type!=PLAYER||disk->level<1||disk->level>60||
       !native_name(disk->name,name)||
       hd79_mount_authoritative_epoch(&set,epoch))goto done;
    a=hd79_mount_find(&set,hd79_mount_a_id);
    b=hd79_mount_find(&set,hd79_mount_b_id);
    c=hd79_mount_find(&set,HD79_MOUNT_PRESENCE_ID);
    e=hd79_mount_find(&set,HD79_AD_DEATH_RECEIPT_ID);
    prior_status=hd79_ad_four_snapshot(&set,epoch,&prior,&priorp,&priord);
    if(mode==0){
        if(prior_status==0){rc=HD79_AD_FOUR_CONFLICT;goto done;}
        if(e>=0)goto done; /* even corrupt/mismatched #83 is not repairable */
        if(prior_status==1){
            if(a>=0||b>=0||c>=0||
               hd79_mount_roster_new(&r,epoch)!=1||
               hd79_presence_new(&r,&p)!=1)goto done;
        } else {
            /* Upgrade only a complete, valid and truly EMPTY 80/81/82.
             * A populated legacy triple has unknowable combat history. */
            if(hd79_presence_snapshot(&set,epoch,&r,&p)!=0 ||
               r.count||r.active_id||a<0||b<0||c<0)goto done;
        }
        if(hd79_ad_death_new_empty(&r,&d)!=1)goto done;
    }else{
        if(prior_status==1){rc=HD79_AD_FOUR_CONFLICT;goto done;}
        if(prior_status!=0||
           !hd79_ad_four_matches(&set,expected,oldp,oldd)){
            if(prior_status==0)rc=HD79_AD_FOUR_CONFLICT;
            goto done;
        }
        r=prior;p=priorp;d=priord;
        if(mode==2){
            if(hd79_ad_death_mark(&r,&d,id,&nextd)!=1){
                if(hd79_ad_death_action_eligible(&r,&d,id)==0)
                    rc=HD79_AD_FOUR_CONFLICT;
                goto done;
            }
            d=nextd;
        }
#ifdef HD79_AD_FOUR_STORE_TESTING
        if(mode==3){
            if(hd79_mount_award(&r,&nextr,r.epoch,species,&awarded)!=1 ||
               hd79_ad_death_award_step(&r,&d,&nextr,&nextd)!=1)goto done;
            nextp=p;
            nextp.count=nextr.count;
            nextp.revision=nextr.revision;
            nextp.active_id=nextr.active_id;
            nextp.room[awarded-1]=room_id;
            if(!hd79_presence_valid(&nextr,&nextp))goto done;
            r=nextr;p=nextp;d=nextd;
        }
#else
        if(mode==3)goto done;
#endif
    }
    if(hd79_mount_wire_encode(&r,wa,wb)||
       hd79_presence_encode(&r,&p,wc)||
       hd79_ad_death_wire_encode(&r,&d,wd))goto done;
    if(mode==0){
        if(a<0 && hd_receipt_add(&set,hd79_mount_a_id,wa))goto done;
        if(b<0 && hd_receipt_add(&set,hd79_mount_b_id,wb))goto done;
        if(c<0 && hd_receipt_add(&set,HD79_MOUNT_PRESENCE_ID,wc))goto done;
        if(hd_receipt_add(&set,HD79_AD_DEATH_RECEIPT_ID,wd))goto done;
    }else{
        if(a<0||b<0||c<0||e<0)goto done;
        memcpy(set.entries[a].manifest_sha256,wa,65);
        memcpy(set.entries[b].manifest_sha256,wb,65);
        memcpy(set.entries[c].manifest_sha256,wc,65);
        memcpy(set.entries[e].manifest_sha256,wd,65);
    }
    if(hd_receipt_encode(raw,HD_RAW_CAPACITY,native,&set,&total))goto done;
    length=hd_compress_bounded((char *)raw,(char *)packed,
                               (int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if(length<1 || length>(int)HD_PLAYER_COMPRESSED_LIMIT)goto done;
    wr=hd_atomic_player_snapshot(PLAYERPATH,name,packed,(size_t)length);
    if(wr==HD_SNAPSHOT_OK||wr==HD_SNAPSHOT_UNCERTAIN){
        if(rout)*rout=r;
        if(pout)*pout=p;
        *dout=d;
        rc=wr==HD_SNAPSHOT_OK?HD79_AD_FOUR_OK:HD79_AD_FOUR_UNCERTAIN;
    }
done:
    if(lock>=0){flock(lock,LOCK_UN);close(lock);}
    free(raw);free(packed);
    return rc;
}
int hd79_ad_four_store_init_empty(const char *name,hd79_mount_roster *r,
                                  hd79_mount_presence *p,
                                  hd79_ad_death_receipt *d)
{
    return hd79_ad_four_transaction(name,0,NULL,NULL,NULL,0,0,0,r,p,d);
}
int hd79_ad_four_store_mark_dead(const char *name,
                                 const hd79_mount_roster *r,
                                 const hd79_mount_presence *p,
                                 const hd79_ad_death_receipt *d,
                                 unsigned id,hd79_ad_death_receipt *out)
{
    return hd79_ad_four_transaction(name,2,r,p,d,id,0,0,NULL,NULL,out);
}
#ifdef HD79_AD_FOUR_STORE_TESTING
int hd79_ad_four_store_test_award(const char *name,
                                  const hd79_mount_roster *r,
                                  const hd79_mount_presence *p,
                                  const hd79_ad_death_receipt *d,
                                  int species,unsigned room_id,
                                  hd79_mount_roster *out_r,
                                  hd79_mount_presence *out_p,
                                  hd79_ad_death_receipt *out_d)
{
    return hd79_ad_four_transaction(name,3,r,p,d,0,species,room_id,
                                    out_r,out_p,out_d);
}
#endif
