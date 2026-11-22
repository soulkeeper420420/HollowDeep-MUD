#ifndef HD_MOUNT_TRAVEL_MOCK_H
#define HD_MOUNT_TRAVEL_MOCK_H
typedef struct hd_mount_profile {
    int species;
    const char *name;
    unsigned endurance_max;
} hd_mount_profile;
const hd_mount_profile *hd_mount_get(int species);
#endif
