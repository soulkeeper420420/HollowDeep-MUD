/* Round79X: private pure request and roster policy regressions. */
#include "hd79_mount_actions.h"
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define EPOCH "1234567890abcdef12345678"

static void parser(void)
{
    hd79_mount_request q,prior;
    const char *bad[][2]={
        {"Mount","1"},{"mount","00"},{"mount","01"},
        {"mount","7"},{"mount","1 2"},{"stable",""},
        {"retrieve","0"},{"stable","-1"},
        {"dismount","1"},{"mount","all"},{"call","1"},
        {"mount","1\nmore"},{"mount","wolf"},
        {"mount","status 1"},{"stable","1;kill"}
    };
    unsigned i;
    assert(hd79_mount_parse("mount","",&q)==1 && q.action==HD79_ACTION_LIST);
    assert(hd79_mount_parse("mount"," list ",&q)==1 && q.action==HD79_ACTION_LIST);
    assert(hd79_mount_parse("mount","\tstatus ",&q)==1 && q.action==HD79_ACTION_STATUS);
    assert(hd79_mount_parse("mount"," 6 ",&q)==1 && q.action==HD79_ACTION_BOARD && q.id==6);
    assert(hd79_mount_parse("dismount"," ",&q)==1 && q.action==HD79_ACTION_DISMOUNT);
    assert(hd79_mount_parse("stable"," 2 ",&q)==1 && q.action==HD79_ACTION_STABLE && q.id==2);
    assert(hd79_mount_parse("retrieve","3",&q)==1 && q.action==HD79_ACTION_RETRIEVE);
    for (i=0;i<sizeof bad/sizeof bad[0];++i) {
        prior=q;
        assert(hd79_mount_parse(bad[i][0],bad[i][1],&q)==-1);
        assert(!memcmp(&q,&prior,sizeof q));
    }
    prior=q;
    assert(hd79_mount_parse(NULL,"",&q)==-1);
    assert(hd79_mount_parse("mount",NULL,&q)==-1);
    assert(!memcmp(&q,&prior,sizeof q));
    puts("PASS: bounded ID-only grammar, malformed/alias/input injection denied");
}
static void transitions(void)
{
    hd79_mount_roster state={0},next,unchanged;
    hd79_mount_request q;
    hd79_mount_context ctx={42,0,1};
    unsigned id;
    assert(hd79_mount_roster_new(&state,EPOCH)==1);
    assert(hd79_mount_award(&state,&next,EPOCH,HD_MOUNT_HORSE,&id)==1);
    state=next;
    assert(hd79_mount_parse("mount","1",&q)==1);
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==1);
    state=next;
    assert(state.active_id==1);
    unchanged=next;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==0);
    assert(!memcmp(&next,&unchanged,sizeof next));
    assert(hd79_mount_parse("stable","1",&q)==1);
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==0);
    ctx.verified_stable=1;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==1);
    state=next;
    assert(state.active_id==0 && state.entries[0].stable_room==42);
    ctx.verified_stable=0;
    assert(hd79_mount_parse("retrieve","1",&q)==1);
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==0);
    ctx.verified_stable=1;
    ctx.room_id=43;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==0);
    ctx.room_id=42;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==1);
    state=next;
    assert(!state.entries[0].stabled && state.entries[0].stable_room==0);
    assert(state.entries[0].endurance==120);
    assert(hd79_mount_parse("mount","status",&q)==1);
    unchanged=next;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==HD79_ACTION_READONLY);
    assert(!memcmp(&next,&unchanged,sizeof next));
    assert(hd79_mount_apply(&state,"aaaaaaaaaaaaaaaaaaaaaaaa",&q,&ctx,&next)==-1);
    ctx.room_id=HD79_MOUNT_MAX_STABLE_ROOM+1;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==-1);
    ctx.room_id=42;
    ctx.verified_stable=2;
    assert(hd79_mount_apply(&state,EPOCH,&q,&ctx,&next)==-1);
    puts("PASS: owner epoch, same-stable locality, presence, no refill and status read only");
}
int main(void)
{
    parser();
    transitions();
    puts("ROUND79X: PURE MOUNT ACTION/SELECTOR POLICY PASS");
    puts("NATIVE DISPATCH AND VERIFIED STABLE WORLD FLAGS: NOT YET INSTALLED");
    return 0;
}
