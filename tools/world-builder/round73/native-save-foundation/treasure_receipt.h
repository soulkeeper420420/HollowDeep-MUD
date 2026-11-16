/* HollowDeep Round 73G: inert native character-save receipt trailer codec.
 * NOT HOOKED TO save_ply/load_ply; DOES NOT GRANT REWARDS.
 * This is a data-format building block only; validate compatibility on ELF32.
 */
#ifndef HD_TREASURE_RECEIPT_H
#define HD_TREASURE_RECEIPT_H
#include <stddef.h>
#define HD_RECEIPT_MAX 64U
#define HD_RECEIPT_CLAIM_LEN 32U
#define HD_RECEIPT_DIGEST_LEN 64U
#define HD_RECEIPT_ENTRY_BYTES (HD_RECEIPT_CLAIM_LEN + HD_RECEIPT_DIGEST_LEN)
#define HD_RECEIPT_TRAILER_MAX (6U + HD_RECEIPT_MAX * HD_RECEIPT_ENTRY_BYTES + 4U)
typedef struct hd_receipt_entry {
    char claim_id[HD_RECEIPT_CLAIM_LEN + 1U];
    char manifest_sha256[HD_RECEIPT_DIGEST_LEN + 1U];
} hd_receipt_entry;
typedef struct hd_receipt_set {
    size_t count;
    hd_receipt_entry entries[HD_RECEIPT_MAX];
} hd_receipt_set;
/* Return 0 on success, -1 if malformed or capacity exceeded. All calls
 * leave the destination unchanged on rejection. */
int hd_receipt_add(hd_receipt_set *set, const char *claim_id,
                   const char *manifest_sha256);
/* Return 1 if exact matching claim/digest exists, 0 if absent, -1 on conflict. */
int hd_receipt_lookup(const hd_receipt_set *set, const char *claim_id,
                      const char *manifest_sha256);
/* Format: [original raw Mordor payload][HDTR1][count:1]
 *         [claim_id:32 digest:64] * count [CRC32:4 big-endian]
 * Unmodified legacy files have no trailer and decode to empty set.
 * Trailing data after the exact trailer is forbidden.
 * The CRC detects accidental corruption, NOT a cryptographic signature.
 * Encoded receipt bytes are part of the SAME compressed player stream;
 * atomic save & safe decompress/serialize remain separate prerequisites. */
int hd_receipt_encode(unsigned char *raw, size_t capacity, size_t native_used,
                      const hd_receipt_set *set, size_t *total_used);
int hd_receipt_decode(const unsigned char *raw, size_t raw_used,
                      size_t native_used, hd_receipt_set *set);
#endif
