#include "treasure_receipt.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static char a[33], b[33], d[65], alt[65];
static unsigned char raw[100000];

int main(void) {
    hd_receipt_set r, saved, sentinel;
    size_t used, n = 137, i;
    memset(&r, 0, sizeof r);
    memset(raw, 0x35, sizeof raw);
    memset(a, 'a', 32); a[32] = '\0';
    memset(b, 'b', 32); b[32] = '\0';
    memset(d, 'd', 64); d[64] = '\0';
    memset(alt, 'e', 64); alt[64] = '\0';
    assert(hd_receipt_decode(raw, n, n, &saved) == 0 && saved.count == 0);
    assert(hd_receipt_encode(raw, sizeof raw, n, &r, &used) == 0 && used == n);
    assert(hd_receipt_add(&r, a, d) == 0);
    assert(hd_receipt_add(&r, a, d) == 0 && r.count == 1);
    assert(hd_receipt_add(&r, a, alt) == -1 && r.count == 1);
    assert(hd_receipt_add(&r, "bad", d) == -1);
    assert(hd_receipt_lookup(&r, a, d) == 1);
    assert(hd_receipt_lookup(&r, b, d) == 0);
    assert(hd_receipt_add(&r, b, alt) == 0);
    assert(hd_receipt_encode(raw, sizeof raw, n, &r, &used) == 0);
    memset(&saved, 0, sizeof saved);
    assert(hd_receipt_decode(raw, used, n, &saved) == 0 && saved.count == 2);
    assert(hd_receipt_lookup(&saved, b, alt) == 1);
    sentinel = saved;
    assert(hd_receipt_decode(raw, used - 1, n, &saved) == -1);
    assert(saved.count == sentinel.count); /* fail atomic */
    assert(hd_receipt_decode(raw, used + 1, n, &saved) == -1);
    raw[n + 8] ^= 0x01;
    assert(hd_receipt_decode(raw, used, n, &saved) == -1);
    raw[n + 8] ^= 0x01;
    assert(hd_receipt_decode(raw, used, n, &saved) == 0);
    assert(hd_receipt_encode(raw, n + 3, n, &r, &used) == -1);
    assert(hd_receipt_decode(raw, n + 1, n, &saved) == -1);
    memset(&r, 0, sizeof r);
    for (i = 0; i < HD_RECEIPT_MAX; ++i) {
        char id[33];
        snprintf(id, sizeof id, "%032x", (unsigned int)i);
        assert(hd_receipt_add(&r, id, d) == 0);
    }
    assert(hd_receipt_add(&r, a, d) == -1);
    assert(hd_receipt_encode(raw, sizeof raw, n, &r, &used) == 0);
    assert(hd_receipt_decode(raw, used, n, &saved) == 0);
    assert(saved.count == HD_RECEIPT_MAX);
    puts("ROUND 73G NATIVE RECEIPT TRAILER: 64-entry/legacy/corruption/replay PASS");
    return 0;
}
