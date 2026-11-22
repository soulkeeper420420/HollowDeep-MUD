/* Round 79G: wilderness mount terrain and endurance-only travel rules. */
#include "hd_mount_travel.h"
#include "hd_wilderness_breath.h"
#include <string.h>

static const hd_mount_profile profiles[] = {
    { HD_MOUNT_HORSE, "Horse", 120, 1, ".=F", 0 },
    { HD_MOUNT_WARHORSE, "Warhorse", 140, 1, ".=FS#", 0 },
    { HD_MOUNT_DIRE_WOLF, "Dire wolf", 130, 1, ".=F^S#", 0 },
    { HD_MOUNT_NIGHTMARE, "Nightmare", 160, 1, ".=F^S#", 0 },
    { HD_MOUNT_GRIFFIN, "Griffin", 175, 2, "F.^S~=#", 1 },
    { HD_MOUNT_DARK_DRAGON, "Dark dragon", 220, 1, "F.^S~=#", 1 }
};

const hd_mount_profile *hd_mount_get(int species)
{
    unsigned index;
    if (species<HD_MOUNT_HORSE || species>HD_MOUNT_DARK_DRAGON)
        return 0;
    index=(unsigned)(species-HD_MOUNT_HORSE);
    return &profiles[index];
}

static int terrain_valid(char terrain)
{
    return terrain && strchr("F.^S~=#", terrain) != 0;
}

static int heavy_terrain(char terrain)
{
    return terrain=='F' || terrain=='S' ||
           terrain=='^' || terrain=='#';
}

int hd_mount_travel_preview(int species, int wilderness, char terrain,
                            unsigned player_breath, unsigned mount_endurance,
                            hd_travel_plan *out)
{
    hd_travel_plan prepared;
    const hd_mount_profile *profile=hd_mount_get(species);
    unsigned cost;
    if (!out || (wilderness!=0 && wilderness!=1) ||
        species<HD_MOUNT_FOOT || species>HD_MOUNT_DARK_DRAGON ||
        player_breath>HD_BREATH_MAX ||
        (species==HD_MOUNT_FOOT && mount_endurance!=0) ||
        (profile && mount_endurance>profile->endurance_max))
        return -1;
    if (wilderness && !terrain_valid(terrain))
        return -1;

    memset(&prepared,0,sizeof prepared);
    prepared.species=species;
    prepared.destination_is_wilderness=wilderness;
    prepared.terrain=wilderness ? terrain : 0;
    prepared.expected_player_breath=player_breath;
    prepared.expected_mount_endurance=mount_endurance;

    if (!wilderness) {
        prepared.resource=HD_TRAVEL_FREE;
        *out=prepared;
        return 1;
    }
    if (!profile) {
        cost=HD_BREATH_WILDERNESS_MOVE_COST;
        if (player_breath<cost) return 0;
        prepared.resource=HD_TRAVEL_PLAYER_BREATH;
    } else {
        if (!strchr(profile->allowed_terrain,terrain)) return 0;
        cost=profile->base_step_cost;
        if (!profile->can_fly && heavy_terrain(terrain))
            ++cost;
        if (mount_endurance<cost) return 0;
        prepared.resource=HD_TRAVEL_MOUNT_ENDURANCE;
    }
    prepared.cost=cost;
    *out=prepared;
    return 1;
}

int hd_mount_travel_finish(const hd_travel_plan *plan,
                           unsigned player_breath, unsigned mount_endurance,
                           int succeeded, unsigned *next_player_breath,
                           unsigned *next_mount_endurance)
{
    hd_travel_plan check;
    unsigned next_player=player_breath, next_mount=mount_endurance;
    int allowed;
    if (!plan || !next_player_breath || !next_mount_endurance ||
        (succeeded!=0 && succeeded!=1) ||
        player_breath!=plan->expected_player_breath ||
        mount_endurance!=plan->expected_mount_endurance)
        return -1;
    allowed=hd_mount_travel_preview(
        plan->species,plan->destination_is_wilderness,plan->terrain,
        player_breath,mount_endurance,&check);
    if (allowed!=1 ||
        check.resource!=plan->resource || check.cost!=plan->cost)
        return -1;
    if (!succeeded) return 0;
    if (plan->resource==HD_TRAVEL_PLAYER_BREATH)
        next_player-=plan->cost;
    else if (plan->resource==HD_TRAVEL_MOUNT_ENDURANCE)
        next_mount-=plan->cost;

    *next_player_breath=next_player;
    *next_mount_endurance=next_mount;
    return 1;
}
