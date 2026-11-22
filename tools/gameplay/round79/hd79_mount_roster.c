/* Round79S: deterministic epoch-bound mount roster without I/O.
 * No static player-pointers, native creature/object ABI changes, or
 * remote stable/mount ownership writes. Persistence/CAS still pending.
 */
#include "hd79_mount_roster.h"
#include <string.h>
#include <stdint.h>

static int epoch_valid(const char *value)
{
    unsigned i,nonzero=0;
    if (!value) return 0;
    for(i=0;i<HD79_MOUNT_EPOCH_CHARS;i++) {
        unsigned char ch=(unsigned char)value[i];
        if (ch>='0' && ch<='9') {
            if (ch!='0') nonzero=1;
        } else if (ch>='a' && ch<='f') {
            nonzero=1;
        } else return 0;
    }
    return nonzero && value[HD79_MOUNT_EPOCH_CHARS]=='\0';
}
int hd79_mount_roster_valid(const hd79_mount_roster *roster)
{
    unsigned i,active_found=0;
    if (!roster || !epoch_valid(roster->epoch) ||
        roster->revision<1 || roster->count>HD79_MOUNT_MAX_OWNED)
        return 0;
    for(i=0;i<roster->count;i++) {
        const hd79_owned_mount *m=&roster->entries[i];
        const hd_mount_profile *profile=hd_mount_get(m->species);
        if (!profile || m->id!=i+1 || m->endurance>profile->endurance_max ||
            m->stabled>1 || (m->stabled && !m->stable_room) ||
            (!m->stabled && m->stable_room))
            return 0;
        if (roster->active_id==m->id) {
            if (m->stabled) return 0;
            active_found=1;
        }
    }
    for(i=roster->count;i<HD79_MOUNT_MAX_OWNED;i++) {
        const hd79_owned_mount *m=&roster->entries[i];
        if (m->id || m->species || m->endurance || m->stabled ||
            m->stable_room)
            return 0;
    }
    return roster->active_id==0 || active_found;
}
int hd79_mount_roster_new(hd79_mount_roster *out,const char *epoch)
{
    hd79_mount_roster fresh;
    if (!out || !epoch_valid(epoch)) return -1;
    memset(&fresh,0,sizeof fresh);
    memcpy(fresh.epoch,epoch,HD79_MOUNT_EPOCH_CHARS+1U);
    fresh.revision=1;
    *out=fresh;
    return 1;
}
static int expected_valid(const hd79_mount_roster *expected,
                          const char *epoch)
{
    if (!hd79_mount_roster_valid(expected) || !epoch_valid(epoch))
        return -1;
    return strcmp(expected->epoch,epoch)==0 ? 1:-1;
}
static int update_allowed(const hd79_mount_roster *expected)
{
    return expected->revision<UINT32_MAX;
}
int hd79_mount_award(const hd79_mount_roster *expected,
                     hd79_mount_roster *next,const char *epoch,
                     int species,unsigned *new_id)
{
    hd79_mount_roster state;
    const hd_mount_profile *profile;
    hd79_owned_mount *m;
    if (!expected || !next || !new_id ||
        expected_valid(expected,epoch)<0 ||
        !update_allowed(expected))
        return -1;
    profile=hd_mount_get(species);
    if (!profile) return -1;
    if (expected->count==HD79_MOUNT_MAX_OWNED) return 0;
    state=*expected;
    m=&state.entries[state.count];
    m->id=state.count+1;
    m->species=species;
    m->endurance=profile->endurance_max;
    m->stabled=0;
    m->stable_room=0;
    state.count++;
    state.revision++;
    *next=state;
    *new_id=m->id;
    return 1;
}
int hd79_mount_board(const hd79_mount_roster *expected,
                     hd79_mount_roster *next,const char *epoch,
                     unsigned id,int present)
{
    hd79_mount_roster state;
    if (!expected || !next || expected_valid(expected,epoch)<0 ||
        id<1 || id>expected->count || (present!=0 && present!=1))
        return -1;
    if (!present || expected->entries[id-1].stabled ||
        expected->active_id==id ||
        expected->active_id!=0)
        return 0;
    if (!update_allowed(expected)) return -1;
    state=*expected;
    state.active_id=id;
    state.revision++;
    *next=state;
    return 1;
}
int hd79_mount_dismount(const hd79_mount_roster *expected,
                        hd79_mount_roster *next,const char *epoch)
{
    hd79_mount_roster state;
    if (!expected || !next || expected_valid(expected,epoch)<0)
        return -1;
    if (!expected->active_id) return 0;
    if (!update_allowed(expected)) return -1;
    state=*expected;
    state.active_id=0;
    state.revision++;
    *next=state;
    return 1;
}
int hd79_mount_stable(const hd79_mount_roster *expected,
                      hd79_mount_roster *next,const char *epoch,
                      unsigned id,unsigned stable_room,
                      int verified_stable,int present)
{
    hd79_mount_roster state;
    if (!expected || !next || expected_valid(expected,epoch)<0 ||
        id<1 || id>expected->count || !stable_room ||
        (verified_stable!=0 && verified_stable!=1) ||
        (present!=0 && present!=1))
        return -1;
    if (!verified_stable || !present ||
        expected->entries[id-1].stabled)
        return 0;
    if (!update_allowed(expected)) return -1;
    state=*expected;
    state.entries[id-1].stabled=1;
    state.entries[id-1].stable_room=stable_room;
    if (state.active_id==id) state.active_id=0;
    state.revision++;
    *next=state;
    return 1;
}
int hd79_mount_retrieve(const hd79_mount_roster *expected,
                        hd79_mount_roster *next,const char *epoch,
                        unsigned id,unsigned stable_room,
                        int verified_stable)
{
    hd79_mount_roster state;
    if (!expected || !next || expected_valid(expected,epoch)<0 ||
        id<1 || id>expected->count || !stable_room ||
        (verified_stable!=0 && verified_stable!=1))
        return -1;
    if (!verified_stable || !expected->entries[id-1].stabled ||
        expected->entries[id-1].stable_room!=stable_room)
        return 0;
    if (!update_allowed(expected)) return -1;
    state=*expected;
    state.entries[id-1].stabled=0;
    state.entries[id-1].stable_room=0;
    state.revision++;
    *next=state;
    return 1;
}
int hd79_mount_travel(const hd79_mount_roster *expected,
                      hd79_mount_roster *next,const char *epoch,
                      const hd_travel_plan *plan,
                      unsigned player_breath,int succeeded,
                      unsigned *next_player_breath)
{
    hd79_mount_roster state;
    const hd79_owned_mount *selected;
    unsigned breath_after,endurance_after;
    int result;
    if (!expected || !next || !plan || !next_player_breath ||
        expected_valid(expected,epoch)<0 ||
        !expected->active_id ||
        (succeeded!=0 && succeeded!=1))
        return -1;
    selected=&expected->entries[expected->active_id-1];
    if (selected->stabled || selected->species!=plan->species ||
        plan->expected_player_breath!=player_breath ||
        plan->expected_mount_endurance!=selected->endurance ||
        (plan->destination_is_wilderness &&
         plan->resource!=HD_TRAVEL_MOUNT_ENDURANCE) ||
        (!plan->destination_is_wilderness &&
         plan->resource!=HD_TRAVEL_FREE))
        return -1;
    result=hd_mount_travel_finish(plan,player_breath,
                                  selected->endurance,succeeded,
                                  &breath_after,&endurance_after);
    if (result<=0) return result;
    if (breath_after!=player_breath) return -1;
    state=*expected;
    if (endurance_after!=selected->endurance) {
        if (!update_allowed(expected)) return -1;
        state.entries[expected->active_id-1].endurance=endurance_after;
        state.revision++;
    }
    *next=state;
    *next_player_breath=breath_after;
    return 1;
}
