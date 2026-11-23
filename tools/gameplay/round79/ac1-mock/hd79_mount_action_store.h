#ifndef HD79_MOUNT_ACTION_STORE_MOCK_H
#define HD79_MOUNT_ACTION_STORE_MOCK_H
#include "hd79_mount_actions.h"
#include "hd79_mount_store.h"
#define HD79_ACTION_STORE_OK 0
#define HD79_ACTION_STORE_FAILURE (-1)
#define HD79_ACTION_STORE_ABSENT 1
#define HD79_ACTION_STORE_CONFLICT 2
#define HD79_ACTION_STORE_UNCERTAIN 3
#define HD79_ACTION_STORE_READONLY 4
#define HD79_ACTION_STORE_DENIED 5
int hd79_mount_action_store(const char *name,const hd79_mount_request *request,
                            const hd79_mount_context *context,hd79_mount_roster *out);
#endif
