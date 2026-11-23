/* Round 79AA: PURE location/physical-presence policy. No native hooks.
 * A third reserved receipt candidate 82 is NOT allocated by this module.
 * Native storage integration must atomically CAS receipts 80,81,82.
 */
#ifndef HD79_MOUNT_PRESENCE_H
#define HD79_MOUNT_PRESENCE_H
#include "hd79_mount_roster.h"
#include <stdint.h>

#define HD79_PRESENCE_RECEIPT_HEX 64U
#define HD79_PRESENCE_MAX_ROOM 0xffffffU
/* These values are NOT user command codes or trusted credentials. */
#define HD79_PRESENCE_BOARD 1U
#define HD79_PRESENCE_DISMOUNT 2U
#define HD79_PRESENCE_STABLE 3U
#define HD79_PRESENCE_RETRIEVE 4U

/* A physical room is 1..0xffffff for an unstabled, unmounted mount.
 * Room zero means mounted, stabled, or not owned. The primary roster
 * remains authoritative for count/active/stable data and owner epoch.
 */
typedef struct hd79_mount_presence {
    uint32_t revision;
    unsigned count;
    unsigned active_id;
    unsigned room[HD79_MOUNT_MAX_OWNED];
} hd79_mount_presence;

/* Empty-roster initialization only. Never auto-migrate a populated
 * roster with missing location receipts: that would summon mounts.
 */
int hd79_presence_new(const hd79_mount_roster *empty,
                      hd79_mount_presence *out);
int hd79_presence_valid(const hd79_mount_roster *roster,
                        const hd79_mount_presence *presence);

/* Canonical one-receipt wire, exactly 32 bytes as 64 lowercase hex:
 * 0: magic 'P'; 1: version 1; 2: count; 3: active ID;
 * 4..7: roster revision BE; 8..25: six room IDs, 24-bit BE;
 * 26..27: zero reserved; 28..31: IEEE CRC32 of bytes 0..27.
 * Room validity depends on simultaneously verified primary roster.
 */
int hd79_presence_encode(const hd79_mount_roster *roster,
                         const hd79_mount_presence *presence,
                         char out[65]);
int hd79_presence_decode(const hd79_mount_roster *roster,
                         const char *receipt,hd79_mount_presence *out);

/* 1 success, 0 denied, -1 malformed. Output unchanged except on 1.
 * Caller must independently verify exact native room/physical entity
 * and stable authority. This policy cannot make client assertions trusted.
 * Next roster must be a valid, exact policy transition of prior roster.
 * Only board/dismount/stable/retrieve are covered; new ownership awards
 * and mounted travel require a separate, atomic location-aware writer.
 */
int hd79_presence_step(const hd79_mount_roster *before,
                       const hd79_mount_presence *old_positions,
                       const hd79_mount_roster *after,
                       unsigned action,unsigned mount_id,
                       unsigned player_room,int native_mount_present,
                       int verified_stable,
                       hd79_mount_presence *new_positions);
#endif
