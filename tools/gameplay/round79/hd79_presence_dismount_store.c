/* Round79AC1: fail-closed, three-receipt atomic dismount.
 * No board, stable, retrieval, awards, mount spawns or movement here.
 * Character room must come from a verified native live creature.
 */
#include "hd79_presence_dismount_store.h"
#include "hd79_mount_wire.h"
#include <string.h>

/* Compare canonical 80/81/82 wire, NOT structure padding. */
static int triple_equal(const hd79_mount_roster *a,
                        const hd79_mount_presence *ap,
                        const hd79_mount_roster *b,
                        const hd79_mount_presence *bp)
{
    char a80[65],a81[65],a82[65],b80[65],b81[65],b82[65];
    if (hd79_mount_wire_encode(a,a80,a81) ||
        hd79_mount_wire_encode(b,b80,b81) ||
        hd79_presence_encode(a,ap,a82) ||
        hd79_presence_encode(b,bp,b82)) return 0;
    return !strcmp(a80,b80) && !strcmp(a81,b81) && !strcmp(a82,b82);
}

int hd79_presence_dismount_store(const char *name,unsigned room,
                                  hd79_mount_roster *out)
{
    hd79_mount_roster before,next,saved,actual;
    hd79_mount_presence before_p,next_p,saved_p,actual_p;
    int rc;
    if (!name || !out || !room || room>HD79_PRESENCE_MAX_ROOM)
        return HD79_DISMOUNT_FAILURE;
    rc=hd79_presence_store_read(name,&before,&before_p);
    if (rc==HD79_PRESENCE_STORE_ABSENT) return HD79_DISMOUNT_ABSENT;
    if (rc!=HD79_PRESENCE_STORE_OK ||
        !hd79_presence_valid(&before,&before_p)) return HD79_DISMOUNT_FAILURE;
    if (!before.active_id) return HD79_DISMOUNT_ON_FOOT;
    rc=hd79_mount_dismount(&before,&next,before.epoch);
    if (rc!=1 ||
        hd79_presence_step(&before,&before_p,&next,HD79_PRESENCE_DISMOUNT,
                           before.active_id,room,0,0,&next_p)!=1)
        return HD79_DISMOUNT_FAILURE;
    rc=hd79_presence_store_commit(name,&before,&before_p,&next,&next_p,
                                  &saved,&saved_p);
    if (rc==HD79_PRESENCE_STORE_OK) {
        if (!triple_equal(&saved,&saved_p,&next,&next_p))
            return HD79_DISMOUNT_FAILURE;
        *out=saved;
        return HD79_DISMOUNT_SUCCESS;
    }
    if (rc==HD79_PRESENCE_STORE_CONFLICT) return HD79_DISMOUNT_CONFLICT;
    if (rc!=HD79_PRESENCE_STORE_UNCERTAIN)
        return HD79_DISMOUNT_FAILURE;
    /* Rename uncertainty: only exact three-receipt state can confirm.
     * No retry or new save here; a mismatch requires reconnect.
     */
    rc=hd79_presence_store_read(name,&actual,&actual_p);
    if (rc!=HD79_PRESENCE_STORE_OK ||
        !triple_equal(&actual,&actual_p,&next,&next_p))
        return HD79_DISMOUNT_UNCERTAIN;
    *out=actual;
    return HD79_DISMOUNT_SUCCESS;
}
