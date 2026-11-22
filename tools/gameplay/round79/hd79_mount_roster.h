/* Round79S: bounded mount ownership/stable transition contract.
 * Engine-independent; no ELF32 creature/object save-ABI changes.
 * Versioned native persistence and atomic player receipt hook TBD.
 */
#ifndef HD79_MOUNT_ROSTER_H
#define HD79_MOUNT_ROSTER_H

#include <stdint.h>
#include "hd_mount_travel.h"

#define HD79_MOUNT_MAX_OWNED 6U
#define HD79_MOUNT_EPOCH_CHARS 24U

typedef struct hd79_owned_mount {
    unsigned id;             /* Owner-local 1..count. Not global creature ID. */
    int species;             /* HD_MOUNT_HORSE .. HD_MOUNT_DARK_DRAGON. */
    unsigned endurance;      /* Resource is separate from character Breath. */
    unsigned stabled;        /* 0 present, 1 in stable, never both. */
    unsigned stable_room;    /* Verified stable identifier while stabled. */
} hd79_owned_mount;

typedef struct hd79_mount_roster {
    char epoch[HD79_MOUNT_EPOCH_CHARS+1U];
    uint32_t revision;       /* Every meaningful roster mutation increments. */
    unsigned count;
    unsigned active_id;      /* 0: on foot; one eligible id when mounted. */
    hd79_owned_mount entries[HD79_MOUNT_MAX_OWNED];
} hd79_mount_roster;

/* 1 valid, 0 invalid. All mutators: 1 changed, 0 no-op/blocked,
 * -1 malformed/stale input. On 0/-1, outputs must remain unchanged.
 * "epoch" must match the actual native character receipt epoch.
 */
int hd79_mount_roster_valid(const hd79_mount_roster *);
int hd79_mount_roster_new(hd79_mount_roster *out,const char *epoch);

int hd79_mount_award(const hd79_mount_roster *expected,
                     hd79_mount_roster *next,const char *epoch,
                     int species,unsigned *new_id);
int hd79_mount_board(const hd79_mount_roster *expected,
                     hd79_mount_roster *next,const char *epoch,
                     unsigned id,int mount_is_present);
int hd79_mount_dismount(const hd79_mount_roster *expected,
                        hd79_mount_roster *next,const char *epoch);
int hd79_mount_stable(const hd79_mount_roster *expected,
                      hd79_mount_roster *next,const char *epoch,
                      unsigned id,unsigned stable_room,
                      int verified_stable,int mount_is_present);
int hd79_mount_retrieve(const hd79_mount_roster *expected,
                        hd79_mount_roster *next,const char *epoch,
                        unsigned id,unsigned stable_room,
                        int verified_stable);

/* PRIVATE policy only. Caller MUST check the native real exit before
 * commit and atomically CAS both moved character and mount receipt
 * under the existing player lock. This function performs NO I/O.
 * Foot travel remains handled by the tested native Breath code.
 */
int hd79_mount_travel(const hd79_mount_roster *expected,
                      hd79_mount_roster *next,const char *epoch,
                      const hd_travel_plan *plan,
                      unsigned player_breath,int native_move_succeeded,
                      unsigned *next_player_breath);
#endif
