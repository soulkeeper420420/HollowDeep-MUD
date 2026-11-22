/* Round79S: deterministic epoch-bound mount ownership/stable policy.
 * Pure rules only: NO native player file/creature pointer/receipt writes.
 */
#include "hd79_mount_roster.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define EPOCH "1234567890abcdef12345678"
#define OTHER "2234567890abcdef12345678"

static void unchanged(const hd79_mount_roster *actual,
                      const hd79_mount_roster *sentinel)
{
    assert(!memcmp(actual,sentinel,sizeof *actual));
}
static void test_epoch_and_invalid(void)
{
    hd79_mount_roster roster={0},untouched;
    assert(hd79_mount_roster_new(&roster,EPOCH)==1);
    assert(hd79_mount_roster_valid(&roster));
    assert(roster.revision==1 && roster.count==0 && roster.active_id==0);
    untouched=roster;
    assert(hd79_mount_roster_new(&roster,"000000000000000000000000")==-1);
    unchanged(&roster,&untouched);
    assert(hd79_mount_roster_new(&roster,"ABCDEFabcdef123456781234")==-1);
    unchanged(&roster,&untouched);
    assert(hd79_mount_roster_new(&roster,"short")==-1);
    unchanged(&roster,&untouched);
    roster.active_id=1;
    assert(!hd79_mount_roster_valid(&roster));
    puts("PASS: epoch identity, empty roster and invalid/forged state rejected");
}
static void test_award_bound_and_no_duplicate_refill(void)
{
    hd79_mount_roster r={0},out={0},saved={0};
    unsigned id=0,blocked_id=99,i;
    assert(hd79_mount_roster_new(&r,EPOCH)==1);
    for(i=0;i<HD79_MOUNT_MAX_OWNED;i++) {
        int species=(int)(i+1);
        const hd_mount_profile *profile=hd_mount_get(species);
        assert(profile);
        assert(hd79_mount_award(&r,&out,EPOCH,species,&id)==1);
        assert(id==i+1 && out.entries[i].id==id);
        assert(out.entries[i].species==species);
        assert(out.entries[i].endurance==profile->endurance_max);
        assert(out.revision==r.revision+1 && out.active_id==0);
        r=out;
    }
    saved=r;
    assert(hd79_mount_award(&r,&out,EPOCH,HD_MOUNT_HORSE,&blocked_id)==0);
    unchanged(&out,&saved);
    assert(blocked_id==99);
    assert(hd79_mount_award(&r,&out,OTHER,HD_MOUNT_HORSE,&blocked_id)==-1);
    unchanged(&out,&saved);
    assert(hd79_mount_award(&r,&out,EPOCH,99,&blocked_id)==-1);
    assert(r.count==6 && hd79_mount_roster_valid(&r));
    puts("PASS: six owned species, hard cap, epoch-bound award, no auto refill");
}
static void test_single_active_mount_and_stable_gate(void)
{
    hd79_mount_roster r={0},next={0},snapshot;
    unsigned first=0,second=0;
    assert(hd79_mount_roster_new(&r,EPOCH)==1);
    assert(hd79_mount_award(&r,&next,EPOCH,HD_MOUNT_HORSE,&first)==1);
    r=next;
    assert(hd79_mount_award(&r,&next,EPOCH,HD_MOUNT_GRIFFIN,&second)==1);
    r=next;
    assert(first==1 && second==2);

    snapshot=next;
    assert(hd79_mount_board(&r,&next,EPOCH,first,0)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_board(&r,&next,OTHER,first,1)==-1);
    unchanged(&next,&snapshot);
    assert(hd79_mount_board(&r,&next,EPOCH,first,1)==1);
    r=next;
    assert(r.active_id==first);
    snapshot=next;
    assert(hd79_mount_board(&r,&next,EPOCH,second,1)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_board(&r,&next,EPOCH,first,1)==0);
    unchanged(&next,&snapshot);

    assert(hd79_mount_stable(&r,&next,EPOCH,first,901,0,1)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_stable(&r,&next,EPOCH,first,901,1,0)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_stable(&r,&next,EPOCH,first,901,1,1)==1);
    r=next;
    assert(r.entries[0].stabled==1 && r.entries[0].stable_room==901);
    assert(r.active_id==0);
    snapshot=next;
    assert(hd79_mount_board(&r,&next,EPOCH,first,1)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_retrieve(&r,&next,EPOCH,first,902,1)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_retrieve(&r,&next,EPOCH,first,901,0)==0);
    unchanged(&next,&snapshot);
    assert(hd79_mount_retrieve(&r,&next,EPOCH,first,901,1)==1);
    r=next;
    assert(!r.entries[0].stabled && !r.entries[0].stable_room);
    assert(!r.active_id);
    assert(hd79_mount_board(&r,&next,EPOCH,second,1)==1);
    r=next;
    assert(r.active_id==second);
    assert(hd79_mount_dismount(&r,&next,EPOCH)==1);
    r=next;
    assert(!r.active_id);
    snapshot=next;
    assert(hd79_mount_dismount(&r,&next,EPOCH)==0);
    unchanged(&next,&snapshot);
    assert(r.entries[0].endurance==hd_mount_get(HD_MOUNT_HORSE)->endurance_max);
    puts("PASS: one rider, stable locality, no remote retrieval and no Endurance refill");
}
static void test_native_movement_authority_and_endurance(void)
{
    hd79_mount_roster r={0},next={0},snapshot;
    hd_travel_plan plan;
    unsigned id=0,breath_after=777;
    assert(hd79_mount_roster_new(&r,EPOCH)==1);
    assert(hd79_mount_award(&r,&next,EPOCH,HD_MOUNT_HORSE,&id)==1);
    r=next;
    assert(hd79_mount_board(&r,&next,EPOCH,id,1)==1);
    r=next;
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'.',80,120,&plan)==1);
    snapshot=next;

    assert(hd79_mount_travel(&r,&next,EPOCH,&plan,80,0,&breath_after)==0);
    unchanged(&next,&snapshot);
    assert(breath_after==777);
    assert(hd79_mount_travel(&r,&next,OTHER,&plan,80,1,&breath_after)==-1);
    unchanged(&next,&snapshot);
    assert(hd79_mount_travel(&r,&next,EPOCH,&plan,80,1,&breath_after)==1);
    r=next;
    assert(r.entries[0].endurance==119 && breath_after==80);
    assert(r.revision==snapshot.revision+1);
    snapshot=next;
    breath_after=777;
    /* Old Endurance preview rejected after an actual debit. */
    assert(hd79_mount_travel(&r,&next,EPOCH,&plan,80,1,&breath_after)==-1);
    unchanged(&next,&snapshot);
    assert(breath_after==777);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,1,'~',80,119,&plan)==0);
    assert(hd_mount_travel_preview(HD_MOUNT_HORSE,0,'.',80,119,&plan)==1);
    assert(hd79_mount_travel(&r,&next,EPOCH,&plan,80,1,&breath_after)==1);
    assert(next.entries[0].endurance==119 && next.revision==r.revision);
    assert(breath_after==80);
    puts("PASS: native move gating, exactly one Endurance debit and free safe retreat");
}
static void test_exhaustion_forgery_and_revision_overflow(void)
{
    hd79_mount_roster r={0},next={0},sentinel;
    hd_travel_plan plan;
    unsigned id=0,after=77;
    assert(hd79_mount_roster_new(&r,EPOCH)==1);
    assert(hd79_mount_award(&r,&next,EPOCH,HD_MOUNT_DARK_DRAGON,&id)==1);
    r=next;
    assert(hd79_mount_board(&r,&next,EPOCH,id,1)==1);
    r=next;
    r.entries[0].endurance=0;
    assert(hd79_mount_roster_valid(&r));
    assert(hd_mount_travel_preview(HD_MOUNT_DARK_DRAGON,1,'.',80,0,&plan)==0);
    assert(hd_mount_travel_preview(HD_MOUNT_DARK_DRAGON,0,'.',80,0,&plan)==1);
    assert(hd79_mount_travel(&r,&next,EPOCH,&plan,80,1,&after)==1);
    assert(after==80 && next.entries[0].endurance==0);
    r.revision=UINT32_MAX;
    sentinel=next;
    assert(hd79_mount_dismount(&r,&next,EPOCH)==-1);
    unchanged(&next,&sentinel);
    r.entries[0].stabled=1;
    r.entries[0].stable_room=901;
    assert(!hd79_mount_roster_valid(&r));
    puts("PASS: exhaustion blocks wilderness, retreat remains free, corrupt/revision overflow denied");
}
int main(void)
{
    test_epoch_and_invalid();
    test_award_bound_and_no_duplicate_refill();
    test_single_active_mount_and_stable_gate();
    test_native_movement_authority_and_endurance();
    test_exhaustion_forgery_and_revision_overflow();
    puts("ROUND79S: PRIVATE EPOCH-BOUND MOUNT ROSTER POLICY PASS");
    puts("NATIVE MOUNT OWNERSHIP/SAVE/STABLE GAMEPLAY: NOT YET INSTALLED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
