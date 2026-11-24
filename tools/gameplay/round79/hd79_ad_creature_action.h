/* Round79AD R6C: private native receipt/creature reconciler.
 * This cannot be called by a normal player command. Never grants ownership,
 * restores mounts at login, or treats #83 zero death bit as resurrection proof.
 */
#ifndef HD79_AD_CREATURE_ACTION_H
#define HD79_AD_CREATURE_ACTION_H
#include "hd79_ad_four_store.h"
struct creature;
#define HD79_AD_CREATURE_DENIED 0
#define HD79_AD_CREATURE_COMPLETE 1
#define HD79_AD_CREATURE_PENDING 2
#define HD79_AD_CREATURE_INVALID (-1)
/* Exact live pointer proof from process-local registry. Never user supplied. */
struct creature *hd79_ad_native_bound_creature(struct creature *owner,
       unsigned id,const hd79_mount_roster *roster,
       const hd79_mount_presence *position);
/* One private action: 1=receipt AND native state confirmed; 0=no action;
 * 2=durable/physical state uncertain (deny further actions/reconnect);
 * -1=malformed. No public command/handler is installed by this source.
 */
int hd79_ad_creature_action(struct creature *owner,unsigned action,unsigned id);
#endif
