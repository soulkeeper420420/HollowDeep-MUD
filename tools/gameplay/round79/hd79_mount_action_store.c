/* Round79X: private mount action to native atomic receipt adapter.
 * No user-facing native command dispatch is installed by this module.
 */
#include "hd79_mount_action_store.h"
#include "hd79_mount_store.h"
#include "hd79_mount_wire.h"
#include <string.h>

static int same_roster(const hd79_mount_roster *a,const hd79_mount_roster *b)
{
    char a1[65],a2[65],b1[65],b2[65];
    if (hd79_mount_wire_encode(a,a1,a2) ||
        hd79_mount_wire_encode(b,b1,b2)) return 0;
    return !strcmp(a1,b1) && !strcmp(a2,b2);
}
int hd79_mount_action_store(const char *player_name,
                            const hd79_mount_request *request,
                            const hd79_mount_context *context,
                            hd79_mount_roster *out)
{
    hd79_mount_roster before,next,saved,actual;
    int rc;
    if (!player_name || !request || !context || !out) return HD79_ACTION_STORE_FAILURE;
    rc=hd79_mount_store_read(player_name,&before);
    if (rc==HD79_MOUNT_STORE_ABSENT) return HD79_ACTION_STORE_ABSENT;
    if (rc!=HD79_MOUNT_STORE_OK) return HD79_ACTION_STORE_FAILURE;
    rc=hd79_mount_apply(&before,before.epoch,request,context,&next);
    if (rc==HD79_ACTION_READONLY) {
        *out=before;
        return HD79_ACTION_STORE_READONLY;
    }
    if (rc==0) return HD79_ACTION_STORE_DENIED;
    if (rc!=1) return HD79_ACTION_STORE_FAILURE;
    rc=hd79_mount_store_commit(player_name,&before,&next,&saved);
    if (rc==HD79_MOUNT_STORE_OK) {
        *out=saved;
        return HD79_ACTION_STORE_OK;
    }
    if (rc==HD79_MOUNT_STORE_CONFLICT) return HD79_ACTION_STORE_CONFLICT;
    if (rc!=HD79_MOUNT_STORE_UNCERTAIN)
        return HD79_ACTION_STORE_FAILURE;
    /* At an uncertain rename, acknowledge ONLY exact next roster on disk.
     * If state cannot be confirmed, fail closed; caller must reconnect.
     */
    if (hd79_mount_store_read(player_name,&actual)!=HD79_MOUNT_STORE_OK ||
        !same_roster(&actual,&next)) return HD79_ACTION_STORE_UNCERTAIN;
    *out=actual;
    return HD79_ACTION_STORE_OK;
}
