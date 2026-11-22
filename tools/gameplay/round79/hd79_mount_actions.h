/* Round79X: strict command request parsing and trusted-context roster policy.
 * No native dispatch table or user-command registration is installed.
 * Native caller MUST verify stable location and mount presence from game state.
 */
#ifndef HD79_MOUNT_ACTIONS_H
#define HD79_MOUNT_ACTIONS_H
#include "hd79_mount_roster.h"
#define HD79_ACTION_LIST 1
#define HD79_ACTION_STATUS 2
#define HD79_ACTION_BOARD 3
#define HD79_ACTION_DISMOUNT 4
#define HD79_ACTION_STABLE 5
#define HD79_ACTION_RETRIEVE 6
#define HD79_ACTION_READONLY 2

typedef struct hd79_mount_request {
    int action;
    unsigned id;
} hd79_mount_request;

typedef struct hd79_mount_context {
    unsigned room_id; /* native room ID; no client-supplied room ID */
    int verified_stable; /* verified against native world, not a user argument */
    int mount_present; /* verified in same room by native ownership/presence */
} hd79_mount_context;

/* Parse lowercase command + remainder: mount [list|status|ID], dismount,
 * stable ID, retrieve ID. IDs are canonical decimal 1..6. No aliases or
 * name selectors until source command collision and lookup audit completes.
 * Returns 1 on success and -1 on invalid input; output unchanged on error.
 */
int hd79_mount_parse(const char *verb,const char *args,
                     hd79_mount_request *out);

/* Apply only a verified request/context. 1 changed, 2 read-only,
 * 0 blocked/no-op, -1 malformed/stale. Output unchanged except on 1.
 * Award is deliberately absent from player command actions.
 */
int hd79_mount_apply(const hd79_mount_roster *prior,const char *epoch,
                     const hd79_mount_request *request,
                     const hd79_mount_context *context,
                     hd79_mount_roster *next);
#endif
