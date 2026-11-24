/* Round79AD R4: private native pre-removal mount death checkpoint.
 * NO player command, award, login/reconnect, or production deployment.
 * A failed death snapshot never authorizes rematerializing a creature.
 */
#ifndef HD79_AD_COMBAT_DEATH_H
#define HD79_AD_COMBAT_DEATH_H
struct creature;
/* 1=durably checked or already tombstoned, 0=not a bound dead mount,
 * -1=fail-closed (no authority to restore). Hook is private/test-only.
 */
int hd79_ad_combat_death_before_remove(struct creature *creature);
#endif
