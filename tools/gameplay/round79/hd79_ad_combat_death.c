/* R4 private native bridge: invoked on del_crt_rom only while hpcur<=0.
 * Dead mount snapshots are retained monotonically under the R3 player lock.
 * The staged native die() gate retains a pending dead mount on failed saves,
 * before native rewards/unlink/free. Reconnect is always denied.
 * Actual combat coverage, cross-process crash recovery and all player
 * commands MUST pass later integration gates before gameplay is exposed.
 */
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_combat_death.h"
#include "hd79_ad_four_store.h"
#include "hd79_mount_world_identity.h"
#include "hd79_mount_wire.h"
#include <string.h>

/* This is added to the *private* identity header during guarded staging. */
#ifndef HD79_AD_DEATH_IDENTITY_PROTOTYPE
#define HD79_AD_DEATH_IDENTITY_PROTOTYPE
extern int hd79_ad_death_identity(creature *,creature **,unsigned *,char [25]);
#endif

static int same_four(const hd79_mount_roster *a,
                     const hd79_mount_presence *ap,
                     const hd79_ad_death_receipt *ad,
                     const hd79_mount_roster *b,
                     const hd79_mount_presence *bp,
                     const hd79_ad_death_receipt *bd)
{
    char a0[65],a1[65],a2[65],a3[65];
    char b0[65],b1[65],b2[65],b3[65];
    if(hd79_mount_wire_encode(a,a0,a1) ||
       hd79_mount_wire_encode(b,b0,b1) ||
       hd79_presence_encode(a,ap,a2) ||
       hd79_presence_encode(b,bp,b2) ||
       hd79_ad_death_wire_encode(a,ad,a3) ||
       hd79_ad_death_wire_encode(b,bd,b3))return 0;
    return !strcmp(a0,b0)&&!strcmp(a1,b1)&&
           !strcmp(a2,b2)&&!strcmp(a3,b3);
}

int hd79_ad_combat_death_before_remove(creature *dead)
{
    creature *owner=NULL;
    unsigned mount_id=0;
    char native_epoch[HD79_MOUNT_EPOCH_CHARS+1U];
    hd79_mount_roster before,actual;
    hd79_mount_presence position,observed_position;
    hd79_ad_death_receipt old_death,expect_death,actual_death,candidate;
    int rc;
    if(!dead || dead->type!=MONSTER || dead->hpcur>0) return 0;
    if(hd79_ad_death_identity(dead,&owner,&mount_id,native_epoch)!=1)
        return 0;
    if(!owner || hd79_ad_four_store_read(owner->name,&before,&position,
                                          &old_death)!=HD79_AD_FOUR_OK)
        return -1;
    if(!hd79_presence_valid(&before,&position) ||
       strcmp(before.epoch,native_epoch) ||
       !mount_id || mount_id>before.count ||
       before.active_id || before.entries[mount_id-1].stabled ||
       position.room[mount_id-1]!=(unsigned)dead->rom_num ||
       before.entries[mount_id-1].species<HD_MOUNT_HORSE ||
       before.entries[mount_id-1].species>HD_MOUNT_DARK_DRAGON)
        return -1;
    /* Exact identity and live native room are checked once more after
     * disk read, immediately before attempting the locked death CAS. */
    {
        creature *fresh_owner=NULL;
        unsigned fresh_id=0;
        char fresh_epoch[HD79_MOUNT_EPOCH_CHARS+1U];
        if(hd79_ad_death_identity(dead,&fresh_owner,&fresh_id,
                                  fresh_epoch)!=1 ||
           fresh_owner!=owner || fresh_id!=mount_id ||
           strcmp(fresh_epoch,native_epoch))return -1;
    }
    if(!hd79_ad_death_valid(&before,&old_death)) return -1;
    if(old_death.dead_mask & (1U<<(mount_id-1)))
        return 1; /* Already durably marked; do not rewrite/duplicate. */
    if(hd79_ad_death_mark(&before,&old_death,mount_id,&expect_death)!=1)
        return -1;
    rc=hd79_ad_four_store_mark_dead(owner->name,&before,&position,
                                    &old_death,mount_id,&candidate);
    if(rc!=HD79_AD_FOUR_OK && rc!=HD79_AD_FOUR_UNCERTAIN)
        return -1;
    /* An uncertain rename is NEVER acknowledged from the return code
     * alone. Read *all four* canonical records and compare exact outcome. */
    if(hd79_ad_four_store_read(owner->name,&actual,&observed_position,
                               &actual_death)!=HD79_AD_FOUR_OK ||
       !same_four(&before,&position,&expect_death,
                  &actual,&observed_position,&actual_death))
        return -1;
    return 1;
}
