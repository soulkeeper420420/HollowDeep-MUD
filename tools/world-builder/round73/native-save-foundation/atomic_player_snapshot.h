/* Round 73G, PRIVATE foundation only. Not linked into HollowDeep game.
 * Accepts already-validated, serialized, COMPRESSED player bytes.
 * Must only be called after bounded serialization + compression succeeds.
 */
#ifndef HD_ATOMIC_PLAYER_SNAPSHOT_H
#define HD_ATOMIC_PLAYER_SNAPSHOT_H
#include <stddef.h>
#define HD_PLAYER_COMPRESSED_LIMIT 49999U
#define HD_SNAPSHOT_ERROR (-1) /* old primary not replaced */
#define HD_SNAPSHOT_OK 0       /* rename + parent fsync succeeded */
#define HD_SNAPSHOT_UNCERTAIN 1 /* rename succeeded; parent sync uncertain */
int hd_atomic_player_snapshot(const char *player_dir, const char *player_name,
                              const unsigned char *compressed, size_t size);
#endif
