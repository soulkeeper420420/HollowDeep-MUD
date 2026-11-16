/* Portable Round 73G standalone receipt trailer codec; no live integration. */
#include "treasure_receipt.h"
#include <stdint.h>
#include <string.h>

#define HD_HEADER_BYTES 6U
#define HD_CRC_BYTES 4U
static const unsigned char hd_magic[5] = { 'H','D','T','R','1' };

static int hd_hex(const char *value, size_t len) {
    size_t i;
    if (!value) return 0;
    for (i = 0; i < len; ++i) {
        if (value[i] == '\0') return 0;
        if (!((value[i] >= '0' && value[i] <= '9') ||
              (value[i] >= 'a' && value[i] <= 'f'))) return 0;
    }
    return value[len] == '\0';
}
static int hd_valid(const hd_receipt_set *set) {
    size_t i, j;
    if (!set || set->count > HD_RECEIPT_MAX) return 0;
    for (i = 0; i < set->count; ++i) {
        if (!hd_hex(set->entries[i].claim_id, HD_RECEIPT_CLAIM_LEN) ||
            !hd_hex(set->entries[i].manifest_sha256, HD_RECEIPT_DIGEST_LEN))
            return 0;
        for (j = 0; j < i; ++j)
            if (!strcmp(set->entries[i].claim_id, set->entries[j].claim_id))
                return 0;
    }
    return 1;
}
static uint32_t hd_crc(const unsigned char *buf, size_t n) {
    uint32_t crc = UINT32_C(0xffffffff);
    size_t i;
    unsigned int j;
    for (i = 0; i < n; ++i) {
        crc ^= buf[i];
        for (j = 0; j < 8U; ++j)
            crc = (crc >> 1) ^ ((crc & 1U) ? UINT32_C(0xedb88320) : 0U);
    }
    return ~crc;
}
static void hd_store32(unsigned char *b, uint32_t n) {
    b[0] = (unsigned char)(n >> 24);
    b[1] = (unsigned char)(n >> 16);
    b[2] = (unsigned char)(n >> 8);
    b[3] = (unsigned char)n;
}
static uint32_t hd_load32(const unsigned char *b) {
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) |
           ((uint32_t)b[2] << 8) | (uint32_t)b[3];
}
int hd_receipt_lookup(const hd_receipt_set *set, const char *claim_id,
                      const char *manifest_sha256) {
    size_t i;
    if (!hd_valid(set) || !hd_hex(claim_id, HD_RECEIPT_CLAIM_LEN) ||
        !hd_hex(manifest_sha256, HD_RECEIPT_DIGEST_LEN)) return -1;
    for (i = 0; i < set->count; ++i) {
        if (!strcmp(set->entries[i].claim_id, claim_id))
            return strcmp(set->entries[i].manifest_sha256, manifest_sha256) ? -1 : 1;
    }
    return 0;
}
int hd_receipt_add(hd_receipt_set *set, const char *claim_id,
                   const char *manifest_sha256) {
    int r = hd_receipt_lookup(set, claim_id, manifest_sha256);
    hd_receipt_entry *entry;
    if (r < 0) return -1;
    if (r == 1) return 0; /* exact replay, no mutation */
    if (set->count == HD_RECEIPT_MAX) return -1;
    entry = &set->entries[set->count];
    memcpy(entry->claim_id, claim_id, HD_RECEIPT_CLAIM_LEN + 1U);
    memcpy(entry->manifest_sha256, manifest_sha256, HD_RECEIPT_DIGEST_LEN + 1U);
    ++set->count;
    return 0;
}
int hd_receipt_encode(unsigned char *raw, size_t capacity, size_t native_used,
                      const hd_receipt_set *set, size_t *total_used) {
    size_t body, required, off, i;
    uint32_t crc;
    if (!raw || !total_used || !hd_valid(set) || native_used > capacity)
        return -1;
    /* Zero receipts need no trailer: preserve byte-for-byte native format. */
    if (set->count == 0) { *total_used = native_used; return 0; }
    body = HD_HEADER_BYTES + HD_RECEIPT_ENTRY_BYTES * set->count;
    required = body + HD_CRC_BYTES;
    if (required > capacity - native_used) return -1;
    off = native_used;
    memcpy(raw + off, hd_magic, sizeof hd_magic);
    raw[off + 5U] = (unsigned char)set->count;
    off += HD_HEADER_BYTES;
    for (i = 0; i < set->count; ++i) {
        memcpy(raw + off, set->entries[i].claim_id, HD_RECEIPT_CLAIM_LEN);
        off += HD_RECEIPT_CLAIM_LEN;
        memcpy(raw + off, set->entries[i].manifest_sha256, HD_RECEIPT_DIGEST_LEN);
        off += HD_RECEIPT_DIGEST_LEN;
    }
    crc = hd_crc(raw + native_used, body);
    hd_store32(raw + off, crc);
    *total_used = off + HD_CRC_BYTES;
    return 0;
}
int hd_receipt_decode(const unsigned char *raw, size_t raw_used,
                      size_t native_used, hd_receipt_set *set) {
    hd_receipt_set parsed;
    size_t length, off, i, expected, n;
    uint32_t stored;
    if (!raw || !set || native_used > raw_used) return -1;
    memset(&parsed, 0, sizeof parsed);
    if (native_used == raw_used) { *set = parsed; return 0; }
    length = raw_used - native_used;
    if (length < HD_HEADER_BYTES + HD_CRC_BYTES ||
        memcmp(raw + native_used, hd_magic, sizeof hd_magic)) return -1;
    n = raw[native_used + 5U];
    if (!n || n > HD_RECEIPT_MAX) return -1;
    expected = HD_HEADER_BYTES + HD_RECEIPT_ENTRY_BYTES * n + HD_CRC_BYTES;
    if (length != expected) return -1;
    stored = hd_load32(raw + native_used + expected - HD_CRC_BYTES);
    if (stored != hd_crc(raw + native_used, expected - HD_CRC_BYTES)) return -1;
    off = native_used + HD_HEADER_BYTES;
    parsed.count = n;
    for (i = 0; i < n; ++i) {
        hd_receipt_entry *e = &parsed.entries[i];
        memcpy(e->claim_id, raw + off, HD_RECEIPT_CLAIM_LEN);
        e->claim_id[HD_RECEIPT_CLAIM_LEN] = '\0';
        off += HD_RECEIPT_CLAIM_LEN;
        memcpy(e->manifest_sha256, raw + off, HD_RECEIPT_DIGEST_LEN);
        e->manifest_sha256[HD_RECEIPT_DIGEST_LEN] = '\0';
        off += HD_RECEIPT_DIGEST_LEN;
    }
    if (!hd_valid(&parsed)) return -1;
    *set = parsed;
    return 0;
}
