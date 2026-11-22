/* Round 79G: pure foot-versus-mount wilderness travel planner.
 * Native mount ownership, movement hooks and persistence NOT included.
 */
#ifndef HD_MOUNT_TRAVEL_H
#define HD_MOUNT_TRAVEL_H

enum hd_mount_species {
    HD_MOUNT_FOOT = 0,
    HD_MOUNT_HORSE = 1,
    HD_MOUNT_WARHORSE = 2,
    HD_MOUNT_DIRE_WOLF = 3,
    HD_MOUNT_NIGHTMARE = 4,
    HD_MOUNT_GRIFFIN = 5,
    HD_MOUNT_DARK_DRAGON = 6
};

enum hd_travel_resource {
    HD_TRAVEL_FREE = 0,
    HD_TRAVEL_PLAYER_BREATH = 1,
    HD_TRAVEL_MOUNT_ENDURANCE = 2
};

typedef struct hd_mount_profile {
    int species;
    const char *name;
    unsigned endurance_max;
    unsigned base_step_cost;
    const char *allowed_terrain;
    unsigned can_fly;
} hd_mount_profile;

typedef struct hd_travel_plan {
    int species;
    int destination_is_wilderness;
    char terrain;
    unsigned resource;
    unsigned cost;
    unsigned expected_player_breath;
    unsigned expected_mount_endurance;
} hd_travel_plan;

/* Returns NULL if species is invalid or FOOT. */
const hd_mount_profile *hd_mount_get(int species);

/* Native map tile terrain: F . ^ S ~ = #.
 * Returns 1 allowed, 0 blocked (terrain or exhaustion), -1 malformed.
 * No mutation on any result; output untouched for blocked/invalid moves.
 */
int hd_mount_travel_preview(int species, int destination_is_wilderness,
                            char terrain, unsigned player_breath,
                            unsigned mount_endurance, hd_travel_plan *out);

/* Only call AFTER the native engine confirms movement succeeded.
 * On success returns 1 and gives new resource totals. On failed movement
 * returns 0 and leaves totals untouched. Invalid/stale prior values = -1,
 * without writing output.
 * Native atomic CAS still needed before this can be used for gameplay.
 */
int hd_mount_travel_finish(const hd_travel_plan *plan,
                           unsigned player_breath, unsigned mount_endurance,
                           int movement_succeeded,
                           unsigned *next_player_breath,
                           unsigned *next_mount_endurance);
#endif
