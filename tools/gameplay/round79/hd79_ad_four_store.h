/* Round79AD R3: private atomic 80/81/82/83 native player snapshot.
 * Death is monotone; all mutable older mount writers fail closed while active.
 * No combat, command, login, travel or production caller is installed.
 */
#ifndef HD79_AD_FOUR_STORE_H
#define HD79_AD_FOUR_STORE_H
#include "hd79_mount_presence.h"
#include "hd79_ad_death_receipt.h"
#define HD79_AD_FOUR_OK 0
#define HD79_AD_FOUR_FAILURE (-1)
#define HD79_AD_FOUR_ABSENT 1
#define HD79_AD_FOUR_CONFLICT 2
#define HD79_AD_FOUR_UNCERTAIN 3

/* Read only: absent only when ALL 80/81/82/83 are missing. */
int hd79_ad_four_store_read(const char *name,hd79_mount_roster *roster,
                            hd79_mount_presence *presence,
                            hd79_ad_death_receipt *death);
/* Fresh four-way allocation, or upgrade EXACTLY empty verified triple.
 * Never fabricate death history for a populated legacy roster. */
int hd79_ad_four_store_init_empty(const char *name,hd79_mount_roster *roster,
                                  hd79_mount_presence *presence,
                                  hd79_ad_death_receipt *death);
/* Native combat caller is NOT wired yet. Requires exact 4-receipt CAS;
 * on uncertainty, caller MUST read back rather than replay the write.
 * Outputs untouched on error, conflict, absent and rename uncertainty
 * except that uncertain exposes the expected candidate for comparison. */
int hd79_ad_four_store_mark_dead(const char *name,
                                 const hd79_mount_roster *expected,
                                 const hd79_mount_presence *expected_presence,
                                 const hd79_ad_death_receipt *expected_death,
                                 unsigned mount_id,
                                 hd79_ad_death_receipt *out_death);

#ifdef HD79_AD_FOUR_STORE_TESTING
/* TEST-ONLY fixture award; absent from the whole native game. Never a
 * player-facing grant. Uses verified room argument solely for test setup. */
int hd79_ad_four_store_test_award(const char *name,
                                  const hd79_mount_roster *expected,
                                  const hd79_mount_presence *expected_presence,
                                  const hd79_ad_death_receipt *expected_death,
                                  int species,unsigned synthetic_room,
                                  hd79_mount_roster *out_roster,
                                  hd79_mount_presence *out_presence,
                                  hd79_ad_death_receipt *out_death);
#endif
#endif
