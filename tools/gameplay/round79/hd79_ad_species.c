/* Private gameplay balance candidate, independent of objmon snapshots.
 * No aggressive, permanent, wander, reward, quest, or spell flags.
 * Terrain, unlock/award policy and Endurance remain in their existing modules.
 */
#include "hd79_ad_species.h"
static const hd79_ad_species_profile species[] = {
    {HD_MOUNT_HORSE,       "Horse",       "horse",     5,  80,10,19,1,4,0},
    {HD_MOUNT_WARHORSE,    "Warhorse",    "warhorse", 15, 180,20,17,2,4,1},
    {HD_MOUNT_DIRE_WOLF,   "Dire wolf",   "wolf",     20, 240,25,16,2,6,2},
    {HD_MOUNT_NIGHTMARE,   "Nightmare",   "nightmare",35, 400,35,14,3,6,3},
    {HD_MOUNT_GRIFFIN,     "Griffin",     "griffin",  40, 480,40,13,3,8,4},
    {HD_MOUNT_DARK_DRAGON, "Dark dragon", "dragon",   55, 800,50,11,4,8,6}
};
const hd79_ad_species_profile *hd79_ad_species_get(int id)
{
    if(id<HD_MOUNT_HORSE || id>HD_MOUNT_DARK_DRAGON) return 0;
    return &species[(unsigned)(id-HD_MOUNT_HORSE)];
}
