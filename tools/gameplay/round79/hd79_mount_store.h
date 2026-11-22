/* Round79W: private native atomic mount roster persistence.
 * This API does not register commands, move characters or deploy.
 * Receipt epoch is bound to the already durable Breath epoch.
 */
#ifndef HD79_MOUNT_STORE_H
#define HD79_MOUNT_STORE_H
#include "hd79_mount_roster.h"
#define HD79_MOUNT_STORE_OK 0
#define HD79_MOUNT_STORE_FAILURE (-1)
#define HD79_MOUNT_STORE_ABSENT 1
#define HD79_MOUNT_STORE_CONFLICT 2
#define HD79_MOUNT_STORE_UNCERTAIN 3

/* Read only. Missing BOTH mount receipts -> ABSENT; half-pairs and
 * corrupted/foreign epochs fail closed with FAILURE.
 */
int hd79_mount_store_read(const char *name, hd79_mount_roster *out);

/* Create an empty roster exactly once under the native player lock.
 * Requires an existing, verified Breath receipt to obtain the epoch.
 */
int hd79_mount_store_init(const char *name, hd79_mount_roster *out);

/* CAS exact expected two-fragment state under native player lock;
 * next must have a revision exactly one greater than expected.
 * Returns UNCERTAIN for an atomic rename with unknown acknowledgement:
 * caller MUST re-read and reconcile before any further mutation.
 */
int hd79_mount_store_commit(const char *name,
                            const hd79_mount_roster *expected,
                            const hd79_mount_roster *next,
                            hd79_mount_roster *out);
#endif
