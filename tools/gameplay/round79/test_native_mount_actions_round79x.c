/* Round79X: real private native mount store action fixture, preserving W tests.
 * Compile only with the disposable ELF32 player fixture, never live saves.
 */
#include "round79w_mount_fixture_base.c"
#include "hd79_mount_actions.h"
#include "hd79_mount_action_store.h"

static void hd79x_parse_req(const char *verb,const char *args,hd79_mount_request *r)
{
    assert(hd79_mount_parse(verb,args,r)==1);
}
static void equal_roster(const hd79_mount_roster *a,const hd79_mount_roster *b)
{
    char a1[65],a2[65],b1[65],b2[65];
    assert(hd79_mount_wire_encode(a,a1,a2)==0);
    assert(hd79_mount_wire_encode(b,b1,b2)==0);
    assert(!strcmp(a1,b1) && !strcmp(a2,b2));
}
int main(void)
{
    const char *who="Hdmtwtest";
    hd79_mount_roster state,next,seen,committed,unchanged;
    hd79_mount_request req;
    hd79_mount_context context={42,0,1};
    unsigned id;
    char *seed[]={0,"seed",NULL};
    (void)seed;
    assert(hd79x_prior_mount_store_test()==0);

    hd79x_parse_req("mount","list",&req);
    assert(hd79_mount_action_store(who,&req,&context,&seen)
           ==HD79_ACTION_STORE_ABSENT);
    assert(hd79_mount_store_init(who,&state)==HD79_MOUNT_STORE_OK);
    assert(hd79_mount_award(&state,&next,state.epoch,
                             HD_MOUNT_HORSE,&id)==1 && id==1);
    assert(hd79_mount_store_commit(who,&state,&next,&committed)
           ==HD79_MOUNT_STORE_OK);
    state=committed;
    puts("PASS: missing roster denied; explicit epoch-bound initialization + award");

    hd79x_parse_req("mount","1",&req);
    assert(hd79_mount_action_store(who,&req,&context,&seen)
           ==HD79_ACTION_STORE_OK);
    assert(seen.active_id==1);
    assert(hd79_mount_store_read(who,&state)==HD79_MOUNT_STORE_OK);
    equal_roster(&seen,&state);
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_DENIED);
    assert(hd79_mount_store_read(who,&committed)==HD79_MOUNT_STORE_OK);
    equal_roster(&committed,&state);
    puts("PASS: exactly one rider, repeated mount does not duplicate revision");

    hd79x_parse_req("stable","1",&req);
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_DENIED);
    context.verified_stable=1;
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_OK);
    state=committed;
    assert(state.active_id==0 && state.entries[0].stable_room==42);
    assert(state.entries[0].endurance==120);
    puts("PASS: stabling requires native-verified same-room stable context");

    hd79x_parse_req("retrieve","1",&req);
    context.room_id=43;
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_DENIED);
    context.room_id=42;
    context.verified_stable=0;
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_DENIED);
    context.verified_stable=1;
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_OK);
    state=committed;
    assert(state.entries[0].stabled==0 && state.entries[0].endurance==120);
    puts("PASS: wrong stable/remote retrieval denied, Endurance not replenished");

    hd79x_parse_req("mount","1",&req);
    assert(hd79_mount_store_read(who,&unchanged)==HD79_MOUNT_STORE_OK);
    setenv("HD_ATOMIC_FAIL","before_rename",1);
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_FAILURE);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_store_read(who,&seen)==HD79_MOUNT_STORE_OK);
    equal_roster(&seen,&unchanged);
    setenv("HD_ATOMIC_FAIL","after_rename",1);
    assert(hd79_mount_action_store(who,&req,&context,&committed)
           ==HD79_ACTION_STORE_OK);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd79_mount_store_read(who,&seen)==HD79_MOUNT_STORE_OK);
    equal_roster(&seen,&committed);
    assert(seen.active_id==1 && seen.revision==unchanged.revision+1);
    puts("PASS: before-rename rollback, after-rename full-roster reconciliation");

    hd79x_parse_req("mount","status",&req);
    assert(hd79_mount_action_store(who,&req,&context,&seen)
           ==HD79_ACTION_STORE_READONLY);
    equal_roster(&seen,&committed);
    hd79x_parse_req("dismount","",&req);
    assert(hd79_mount_action_store(who,&req,&context,&seen)
           ==HD79_ACTION_STORE_OK);
    assert(seen.active_id==0 && seen.entries[0].endurance==120);
    puts("PASS: status read only, dismount persists without Endurance refill");

    puts("ROUND79X: PRIVATE NATIVE ATOMIC MOUNT ACTION BACKEND PASS");
    puts("NATIVE COMMAND DISPATCH / MOUNTED MOVEMENT: NOT YET WIRED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
