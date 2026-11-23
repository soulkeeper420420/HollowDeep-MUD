#ifndef HD79_MOUNT_ACTIONS_MOCK_H
#define HD79_MOUNT_ACTIONS_MOCK_H
#define HD79_ACTION_LIST 1
#define HD79_ACTION_STATUS 2
#define HD79_ACTION_BOARD 3
#define HD79_ACTION_DISMOUNT 4
#define HD79_ACTION_STABLE 5
#define HD79_ACTION_RETRIEVE 6
typedef struct hd79_mount_request { int action; unsigned id; } hd79_mount_request;
typedef struct hd79_mount_context { unsigned room_id; int verified_stable,mount_present; } hd79_mount_context;
int hd79_mount_parse(const char *verb,const char *args,hd79_mount_request *out);
#endif
