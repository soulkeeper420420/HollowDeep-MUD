/* Round79X: private atomic transaction adapter for vetted mount requests.
 * DOES NOT register user commands or authorize stable rooms.
 */
#ifndef HD79_MOUNT_ACTION_STORE_H
#define HD79_MOUNT_ACTION_STORE_H
#include "hd79_mount_actions.h"
#define HD79_ACTION_STORE_OK 0
#define HD79_ACTION_STORE_FAILURE (-1)
#define HD79_ACTION_STORE_ABSENT 1
#define HD79_ACTION_STORE_CONFLICT 2
#define HD79_ACTION_STORE_UNCERTAIN 3
#define HD79_ACTION_STORE_READONLY 4
#define HD79_ACTION_STORE_DENIED 5

/* Read authorized durable roster, apply bounded transition, CAS both
 * receipt fragments once, reconcile uncertain rename by exact full roster.
 * No auto-init or award; callers must separately authorize mount presence
 * and the stable room against native live engine state.
 */
int hd79_mount_action_store(const char *player_name,
                            const hd79_mount_request *request,
                            const hd79_mount_context *context,
                            hd79_mount_roster *out);
#endif
