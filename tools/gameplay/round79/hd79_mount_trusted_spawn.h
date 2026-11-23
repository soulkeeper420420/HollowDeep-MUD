/* Round79AC3C: server-only, unexposed native mount-template spawn backend.
 * Requires prior accepted native presence receipts and lifecycle revocation.
 * NO public command or login/reconnect hook may call this in this milestone.
 */
#ifndef HD79_MOUNT_TRUSTED_SPAWN_H
#define HD79_MOUNT_TRUSTED_SPAWN_H
#include "hd79_mount_presence_store.h"
struct creature;
/* The catalog is constructed by trusted C/server configuration, never from
 * user text or the ownership roster. A zero template ID disables a species.
 * Native template IDs are unknown until verified against the private world.
 */
typedef struct hd79_trusted_mount_catalog {
    int native_template_id[HD79_MOUNT_MAX_OWNED];
} hd79_trusted_mount_catalog;

/* Return 1 on successful real native placement+identity binding, 0 denied,
 * -1 on native load/binding error. *out is changed ONLY on success.
 * A future trusted lifecycle caller must remove/despawn these NPCs on logout
 * and rehydrate from authoritative state on login before enabling gameplay.
 */
int hd79_mount_spawn_trusted(struct creature *owner, unsigned mount_id,
                            const hd79_trusted_mount_catalog *catalog,
                            struct creature **out);
#endif
