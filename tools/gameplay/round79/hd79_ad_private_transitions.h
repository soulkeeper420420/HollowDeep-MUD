/* Round79AD: pure, unexposed native mount action and movement planner.
 * Returns proposed AFTER state only; never commits or changes live world.
 * Server-only caller must prove native pointer/stable authority and perform
 * exact 80/81/82 CAS under the same native character movement checkpoint.
 */
#ifndef HD79_AD_PRIVATE_TRANSITIONS_H
#define HD79_AD_PRIVATE_TRANSITIONS_H
#include "hd79_mount_presence.h"

/* 1 planned, 0 denied/no-op, -1 malformed. Outputs untouched unless 1.
 * action from HD79_PRESENCE_BOARD/DISMOUNT/STABLE/RETRIEVE.
 * native_present and stable_authorized MUST be server-verified, never user text.
 */
int hd79_ad_private_plan_action(
    const hd79_mount_roster *prior,const hd79_mount_presence *where,
    unsigned action,unsigned id,unsigned native_room,
    int native_present,int stable_authorized,
    hd79_mount_roster *next,hd79_mount_presence *next_where);

/* 1 = endurance debit planned, 2 = free confirmed safe retreat with NO
 * receipt change, 0 = movement failed/denied, -1 malformed/stale.
 * Never writes the player file or moves a native creature. Caller MUST
 * commit both native movement and triple receipts atomically or roll back.
 * No public movement hook is installed in this milestone.
 */
int hd79_ad_private_plan_mounted_move(
    const hd79_mount_roster *prior,const hd79_mount_presence *where,
    const hd_travel_plan *preview,unsigned prior_player_breath,
    int native_move_succeeded,
    hd79_mount_roster *next,hd79_mount_presence *next_where,
    unsigned *next_player_breath);
#endif
