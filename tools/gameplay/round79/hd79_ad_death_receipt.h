/* Round79AD R2: pure prospective fourth native 64-hex receipt (#83).
 * NOT wired to player saves. Never supplies enough evidence to restore.
 * CRC detects corruption; protected atomic native player save is required
 * before the record may be regarded as durable evidence.
 */
#ifndef HD79_AD_DEATH_RECEIPT_H
#define HD79_AD_DEATH_RECEIPT_H
#include "hd79_mount_roster.h"
#include <stdint.h>
#define HD79_AD_DEATH_RECEIPT_ID "ffffffffffffffffffffffffffffff83"
#define HD79_AD_DEATH_RECEIPT_HEX 64U
typedef struct hd79_ad_death_receipt {
    char epoch[HD79_MOUNT_EPOCH_CHARS+1U];
    uint32_t serial;
    unsigned count;
    unsigned dead_mask;
} hd79_ad_death_receipt;
/* Starts only with a genuinely empty valid roster, NEVER retrofits any
 * populated older player state with a fabricated 'all alive' receipt. */
int hd79_ad_death_new_empty(const hd79_mount_roster *roster,
                            hd79_ad_death_receipt *out);
int hd79_ad_death_valid(const hd79_mount_roster *roster,
                        const hd79_ad_death_receipt *death);
int hd79_ad_death_wire_encode(const hd79_mount_roster *roster,
                              const hd79_ad_death_receipt *death,
                              char out[65]);
int hd79_ad_death_wire_decode(const hd79_mount_roster *roster,
                              const char *encoded,
                              hd79_ad_death_receipt *out);
/* Only an authenticated, previously persisted death receipt can be passed
 * to this private step, and the caller must prove native death. Future
 * transaction MUST write updated receipt #83 atomically with 80/81/82.
 * Return 1 changed, 0 previously dead, -1 invalid; output otherwise intact. */
int hd79_ad_death_mark(const hd79_mount_roster *roster,
                       const hd79_ad_death_receipt *prior,
                       unsigned id,hd79_ad_death_receipt *next);
/* Authoritative award transition future-only: no gameplay award caller.
 * For a newly increased count, preserve all previous death bits. */
int hd79_ad_death_award_step(const hd79_mount_roster *before,
                             const hd79_ad_death_receipt *prior,
                             const hd79_mount_roster *after,
                             hd79_ad_death_receipt *next);
int hd79_ad_death_action_eligible(const hd79_mount_roster *roster,
                                  const hd79_ad_death_receipt *death,
                                  unsigned id);
/* Deliberately fail closed even on a zero death bitmap: a receipt #83 does
 * not itself prove that a process-local creature survived logout/death. */
int hd79_ad_death_reconnect_allowed(const hd79_mount_roster *roster,
                                    const hd79_ad_death_receipt *death,
                                    unsigned id);
#endif
