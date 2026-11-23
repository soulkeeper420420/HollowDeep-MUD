/* Round79AC2: PRIVATE process-local creature/owner proof, no awards or verbs.
 * Deliberately does NOT spawn creatures or reconstruct identity on login.
 * A later verified spawn/lifecycle hook must bind and unbind these tokens.
 */
#ifndef HD79_MOUNT_WORLD_IDENTITY_H
#define HD79_MOUNT_WORLD_IDENTITY_H
#include "hd79_mount_presence.h"
struct creature;

/* Return 1 only when both live native room lists agree with the durable
 * epoch-bound roster and location receipt. Return 0 otherwise.
 * Binding is a trusted internal API, NEVER a player-command operation.
 */
int hd79_world_mount_bind(struct creature *owner,struct creature *mount,
                           unsigned id,const hd79_mount_roster *roster,
                           const hd79_mount_presence *position);
int hd79_world_mount_present(struct creature *owner,unsigned id,
                              const hd79_mount_roster *roster,
                              const hd79_mount_presence *position);
/* Future mandatory hooks: call before monster removal/free, owner logout.
 * A later milestone must prove all removal paths are covered before any
 * state-changing mount command can consume hd79_world_mount_present.
 */
void hd79_world_mount_unbind_creature(const struct creature *mount);
void hd79_world_mount_unbind_owner(const struct creature *owner);
#endif
