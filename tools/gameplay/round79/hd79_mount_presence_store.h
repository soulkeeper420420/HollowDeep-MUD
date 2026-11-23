/* Round79AB: native three-fragment mount/presence atomic receipt store.
 * PRIVATE feature gate only. No in-game boarding, awards or movement.
 * The old two-fragment writer must be disabled while this is enabled.
 */
#ifndef HD79_MOUNT_PRESENCE_STORE_H
#define HD79_MOUNT_PRESENCE_STORE_H
#include "hd79_mount_presence.h"
#define HD79_MOUNT_PRESENCE_ID "ffffffffffffffffffffffffffffff82"
#define HD79_PRESENCE_STORE_OK 0
#define HD79_PRESENCE_STORE_FAILURE (-1)
#define HD79_PRESENCE_STORE_ABSENT 1
#define HD79_PRESENCE_STORE_CONFLICT 2
#define HD79_PRESENCE_STORE_UNCERTAIN 3

/* ABSENT only if ALL three records are missing. Inconsistent/partial
 * records, populated legacy pair without location or epoch mismatch fail.
 */
int hd79_presence_store_read(const char *name,
                             hd79_mount_roster *roster,
                             hd79_mount_presence *position);
/* Fresh triple creation or explicit safe upgrade of EMPTY legacy pair.
 * NEVER synthesize locations for mounts in a populated legacy roster.
 */
int hd79_presence_store_init(const char *name,
                             hd79_mount_roster *roster,
                             hd79_mount_presence *position);
/* Exact prior three-record CAS; ONE compressed atomic player snapshot.
 * Caller MUST authenticate physical world presence and command context.
 * Success or UNCERTAIN outputs only; uncertain must be reconciled by read.
 */
int hd79_presence_store_commit(const char *name,
                               const hd79_mount_roster *expected,
                               const hd79_mount_presence *expected_position,
                               const hd79_mount_roster *desired,
                               const hd79_mount_presence *desired_position,
                               hd79_mount_roster *out_roster,
                               hd79_mount_presence *out_position);
#endif
