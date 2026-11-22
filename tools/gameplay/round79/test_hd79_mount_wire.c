/* Round79T: pure 2x64-hex receipt integrity regression.
 * Does NOT test actual native player saves. Reserved claim IDs and
 * atomic snapshot integration must be audited before use.
 */
#include "hd79_mount_wire.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define EPOCH "1234567890abcdef12345678"

static void two_fragments_roundtrip(void)
{
    hd79_mount_roster state={0},next={0},read={0};
    char first[65],second[65],repeat_a[65],repeat_b[65];
    unsigned id,i;
    assert(hd79_mount_roster_new(&state,EPOCH)==1);
    for(i=1;i<=HD79_MOUNT_MAX_OWNED;i++) {
        assert(hd79_mount_award(&state,&next,EPOCH,(int)i,&id)==1);
        assert(id==i);
        state=next;
    }
    assert(hd79_mount_board(&state,&next,EPOCH,5,1)==1);
    state=next;
    assert(hd79_mount_stable(&state,&next,EPOCH,3,0xffffffU,1,1)==1);
    state=next;
    assert(hd79_mount_wire_encode(&state,first,second)==0);
    assert(strlen(first)==64 && strlen(second)==64);
    assert(hd79_mount_wire_decode(first,second,&read)==0);
    assert(read.revision==state.revision);
    assert(read.active_id==5 && read.entries[2].stable_room==0xffffffU);
    assert(hd79_mount_roster_valid(&read));
    assert(hd79_mount_wire_encode(&read,repeat_a,repeat_b)==0);
    assert(!strcmp(first,repeat_a) && !strcmp(second,repeat_b));
    puts("PASS: six owned mounts, active mount, max stable room and canonical two-part wire");
}
static void empty_and_partial(void)
{
    hd79_mount_roster s={0},t={0};
    char first[65],second[65];
    assert(hd79_mount_roster_new(&s,EPOCH)==1);
    assert(hd79_mount_wire_encode(&s,first,second)==0);
    assert(hd79_mount_wire_decode(first,second,&t)==0);
    assert(t.count==0 && t.active_id==0 && t.revision==1);
    assert(!strcmp(t.epoch,EPOCH));
    puts("PASS: empty roster roundtrip and original character epoch preserved");
}
static void corruption_no_output(void)
{
    hd79_mount_roster s={0},next={0},out,unchanged;
    char a[65],b[65],mix[65],wrong[66];
    unsigned id;
    assert(hd79_mount_roster_new(&s,EPOCH)==1);
    assert(hd79_mount_award(&s,&next,EPOCH,HD_MOUNT_HORSE,&id)==1);
    s=next;
    assert(hd79_mount_wire_encode(&s,a,b)==0);
    memset(&out,0x5a,sizeof out);
    unchanged=out;

    strcpy(wrong,a);wrong[8]=(wrong[8]=='0'?'1':'0');
    assert(hd79_mount_wire_decode(wrong,b,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));

    strcpy(wrong,b);wrong[14]=(wrong[14]=='0'?'1':'0');
    assert(hd79_mount_wire_decode(a,wrong,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));

    strcpy(wrong,b);wrong[2]='G';
    assert(hd79_mount_wire_decode(a,wrong,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));
    strcpy(wrong,b);wrong[2]='A';
    assert(hd79_mount_wire_decode(a,wrong,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));
    strcpy(wrong,b);wrong[64]='1';wrong[65]=0; /* see below */
    assert(hd79_mount_wire_decode(a,wrong,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));

    strcpy(mix,b);
    assert(hd79_mount_award(&s,&next,EPOCH,HD_MOUNT_GRIFFIN,&id)==1);
    s=next;
    assert(hd79_mount_wire_encode(&s,a,b)==0);
    assert(hd79_mount_wire_decode(a,mix,&out)==-1);
    assert(!memcmp(&out,&unchanged,sizeof out));
    puts("PASS: corruption, uppercase, bad length and mixed-generation receipts fail closed");
}
static void stable_bounds_and_revision(void)
{
    hd79_mount_roster s={0},next={0},snapshot;
    char a[65],b[65];
    unsigned id;
    assert(hd79_mount_roster_new(&s,EPOCH)==1);
    assert(hd79_mount_award(&s,&next,EPOCH,HD_MOUNT_GRIFFIN,&id)==1);
    s=next;
    assert(hd79_mount_stable(&s,&next,EPOCH,id,0x1000000U,1,1)==1);
    s=next;
    strcpy(a,"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
    strcpy(b,"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB");
    assert(hd79_mount_wire_encode(&s,a,b)==-1);
    assert(a[0]=='A' && b[0]=='B');
    snapshot=s;
    s.epoch[0]='z';
    assert(hd79_mount_wire_encode(&s,a,b)==-1);
    s=snapshot;
    /* Restore the largest representable room after the oversized
     * value's intended rejection, then test full revision range. */
    s.entries[0].stable_room=HD79_MOUNT_MAX_STABLE_ROOM;
    s.revision=UINT32_MAX;
    assert(hd79_mount_wire_encode(&s,a,b)==0);
    assert(hd79_mount_wire_decode(a,b,&snapshot)==0);
    assert(snapshot.revision==UINT32_MAX);
    assert(hd79_mount_dismount(&snapshot,&s,EPOCH)==0);
    puts("PASS: out-of-wire stable room/forged epoch denied, full uint32 revision roundtrips");
}
int main(void)
{
    two_fragments_roundtrip();
    empty_and_partial();
    corruption_no_output();
    stable_bounds_and_revision();
    puts("ROUND79T: PRIVATE MOUNT TWO-RECEIPT WIRE CONTRACT PASS");
    puts("NATIVE RESERVED IDS, PLAYER-SAVE CAS AND RECONNECT: NOT YET WIRED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
