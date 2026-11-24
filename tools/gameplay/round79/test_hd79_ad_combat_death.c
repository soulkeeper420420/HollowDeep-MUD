/* R4 fail-closed combat death save bridge: isolated synthetic mock.
 * Real native pointer registry, 32-bit game, socket and R3 native writer
 * are tested separately by the private Linode stage/runner.
 */
#include "hd_player_store.h"
#include "hd79_ad_combat_death.h"
#include "hd79_ad_four_store.h"
#include "hd79_mount_world_identity.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static const char epoch[]="1234567890abcdef12345678";
static creature owner={"PrivateOwner",PLAYER,1,100,100,42};
static creature mount={"HD-private horse",MONSTER,1,1,1,42};
static creature forged={"HD-private horse",MONSTER,1,0,1,42};
static hd79_mount_roster saved;
static hd79_mount_presence position;
static hd79_ad_death_receipt death;
static int owner_valid=1,read_failed=0,read_count=0;
static int save_mode=0,saves=0;
static int tamper_readback=0;

int hd79_ad_death_identity(creature *dead,creature **who,
                           unsigned *id,char out_epoch[25])
{
    if(!owner_valid || dead!=&mount || dead->hpcur>0)return 0;
    *who=&owner;*id=1;memcpy(out_epoch,epoch,25);
    return 1;
}
int hd79_presence_valid(const hd79_mount_roster *r,const hd79_mount_presence *p)
{
    return r && p && r->revision==p->revision &&
           r->count==p->count && r->count==1 &&
           r->entries[0].id==1 && r->entries[0].species==1;
}
int hd79_ad_death_valid(const hd79_mount_roster *r,const hd79_ad_death_receipt *d)
{
    return r && d && !strcmp(r->epoch,d->epoch) &&
           d->serial>0 && d->count==r->count && !(d->dead_mask & ~1U);
}
int hd79_ad_death_mark(const hd79_mount_roster *r,
    const hd79_ad_death_receipt *prior,unsigned id,
    hd79_ad_death_receipt *next)
{
    if(!hd79_ad_death_valid(r,prior) || id!=1 || (prior->dead_mask&1))return -1;
    *next=*prior;next->dead_mask|=1U;next->serial++;
    return 1;
}
int hd79_mount_wire_encode(const hd79_mount_roster *r,char a[65],char b[65])
{
    if(!r || !r->revision || strcmp(r->epoch,epoch))return -1;
    snprintf(a,65,"roster:%u:%u",r->revision,r->count);
    snprintf(b,65,"mount:%u:%d",r->entries[0].id,r->entries[0].species);
    return 0;
}
int hd79_presence_encode(const hd79_mount_roster *r,
                          const hd79_mount_presence *p,char a[65])
{
    if(!hd79_presence_valid(r,p))return -1;
    snprintf(a,65,"presence:%u:%u",p->revision,p->room[0]);
    return 0;
}
int hd79_ad_death_wire_encode(const hd79_mount_roster *r,
    const hd79_ad_death_receipt *d,char a[65])
{
    if(!hd79_ad_death_valid(r,d))return -1;
    snprintf(a,65,"death:%u:%u",d->serial,d->dead_mask);
    return 0;
}
int hd79_ad_four_store_read(const char *name,hd79_mount_roster *r,
    hd79_mount_presence *p,hd79_ad_death_receipt *d)
{
    ++read_count;
    if(read_failed || strcmp(name,owner.name))return HD79_AD_FOUR_FAILURE;
    *r=saved;*p=position;*d=death;
    if(tamper_readback && read_count>=2)
        p->room[0]=43;
    return HD79_AD_FOUR_OK;
}
int hd79_ad_four_store_mark_dead(const char *name,const hd79_mount_roster *r,
    const hd79_mount_presence *p,const hd79_ad_death_receipt *d,
    unsigned id,hd79_ad_death_receipt *out)
{
    hd79_ad_death_receipt advanced;
    ++saves;
    if(strcmp(name,owner.name) || !hd79_presence_valid(r,p) ||
       !hd79_ad_death_valid(r,d) || id!=1)return HD79_AD_FOUR_FAILURE;
    if(save_mode==1)return HD79_AD_FOUR_FAILURE; /* before rename */
    if(save_mode!=3) {
        if(hd79_ad_death_mark(r,d,id,&advanced)!=1)return HD79_AD_FOUR_CONFLICT;
        death=advanced;
        *out=advanced;
    }
    return save_mode==0 ? HD79_AD_FOUR_OK:HD79_AD_FOUR_UNCERTAIN;
}
static void reset(void)
{
    memset(&saved,0,sizeof saved);
    memset(&position,0,sizeof position);
    memset(&death,0,sizeof death);
    memcpy(saved.epoch,epoch,25);saved.revision=3;saved.count=1;
    saved.entries[0].id=1;saved.entries[0].species=1;
    position.revision=3;position.count=1;position.room[0]=42;
    memcpy(death.epoch,epoch,25);death.serial=2;death.count=1;
    read_failed=0;save_mode=0;saves=0;read_count=0;
    owner_valid=1;tamper_readback=0;mount.hpcur=0;
}
int main(void)
{
    reset();mount.hpcur=1;
    assert(hd79_ad_combat_death_before_remove(&mount)==0);
    mount.hpcur=0;
    assert(hd79_ad_combat_death_before_remove(&forged)==0);
    owner_valid=0;
    assert(hd79_ad_combat_death_before_remove(&mount)==0);
    assert(saves==0);
    puts("PASS: living, forged and unregistered pointer cannot tombstone a mount");

    reset();read_failed=1;
    assert(hd79_ad_combat_death_before_remove(&mount)==-1);
    assert(saves==0);
    puts("PASS: missing or corrupt authoritative four-receipt disk snapshot denied");

    reset();save_mode=1;
    assert(hd79_ad_combat_death_before_remove(&mount)==-1);
    assert(death.dead_mask==0 && saves==1);
    puts("PASS: failed before-rename native death snapshot never acknowledged");

    reset();save_mode=3;
    assert(hd79_ad_combat_death_before_remove(&mount)==-1);
    assert(death.dead_mask==0);
    puts("PASS: uncertain native save without matching readback denied");

    reset();save_mode=2;
    assert(hd79_ad_combat_death_before_remove(&mount)==1);
    assert(death.dead_mask==1 && saves==1 && read_count==2);
    assert(hd79_ad_combat_death_before_remove(&mount)==1);
    assert(saves==1);
    puts("PASS: uncertain after-rename reconciles four receipts exactly once");

    reset();tamper_readback=1;
    assert(hd79_ad_combat_death_before_remove(&mount)==-1);
    assert(death.dead_mask==1);
    puts("PASS: mismatched four-receipt post-save readback fails closed");

    reset();death.serial=0;
    assert(hd79_ad_combat_death_before_remove(&mount)==-1);
    assert(saves==0);
    puts("PASS: invalid or fabricated death serial cannot be treated as prior tombstone");

    puts("ROUND79AD R4: PRIVATE NATIVE COMBAT DEATH PRE-REMOVE POLICY PASS");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
