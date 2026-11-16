/* Round 73H: disposable-only durable native guardian evidence.
 * NOT a reward-authorizing service. No player- or web-facing API.
 * A matching name does not prove a creature was the bound instance: the
 * native treasure_guard death callback MUST check the pointer first.
 */
#ifndef HD_GUARD_PROOF_H
#define HD_GUARD_PROOF_H
#include <stdint.h>
#define HD_GPROOF_MAX 5
#define HD_GPROOF_OK 0
#define HD_GPROOF_ALREADY 1
#define HD_GPROOF_ERROR (-1)
#define HD_GPROOF_UNCERTAIN (-2)
typedef struct hd_guard_proof {
    char magic[16];
    uint32_t version;
    uint32_t room;
    uint32_t count;
    char map[33];
    char owner[80];
    char names[HD_GPROOF_MAX][80];
    char encounter_id[33];
    char guardian_ids[HD_GPROOF_MAX][33];
    char event_ids[HD_GPROOF_MAX][33];
    unsigned char dead[HD_GPROOF_MAX];
    uint32_t crc;
} hd_guard_proof;
/* Root is a trusted, existing, owner-controlled, mode-0700 directory.
 * All paths are anchored with openat(O_NOFOLLOW). Both operations lock the
 * directory, fsync the new file and then the parent, and fail closed. */
int hd_guard_proof_begin(const char *root, uint32_t room,
                         const char *map, const char *owner,
                         const char (*names)[80], unsigned count,
                         hd_guard_proof *out);
/* Only the native pointer-verified combat death hook may call this. */
int hd_guard_proof_mark(const char *root, hd_guard_proof *proof,
                        unsigned index);
int hd_guard_proof_ready(const hd_guard_proof *proof);
#endif
