/* Tests the ACTUAL files3.c from the uploaded 73G native save contract.
 * This 64-bit compilation tests record and trailing-length semantics only;
 * it is NOT a replacement for a native ELF32 gameplay replay.
 */
#include "mstruct.h"
#include "treasure_receipt.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
extern int write_crt_to_mem(char *, creature *, int);
extern int read_crt_from_mem(char *, creature *);
#ifdef HD_WITH_ORIGINAL_COMPRESS
extern int compress(char *, char *, int);
extern int uncompress(char *, char *, int);
static unsigned char compressed[100000], unpacked[100000];
#endif

int count_obj(object *obj, int perm_only) {
    otag *p; int total = 0; (void)perm_only;
    for (p = obj->first_obj; p; p = p->next_tag) ++total;
    return total;
}
int count_inv(creature *crt, int perm_only) {
    otag *p; int total = 0; (void)perm_only;
    for (p = crt->first_obj; p; p = p->next_tag) ++total;
    return total;
}
void merror(char *reason, int level) {
    fprintf(stderr, "Unexpected native error: %s (%d)\n", reason, level);
    abort();
}
static void free_objects(otag *tag) {
    while (tag) {
        otag *next = tag->next_tag;
        if (tag->obj) { free_objects(tag->obj->first_obj); free(tag->obj); }
        free(tag);
        tag = next;
    }
}
int main(void) {
    creature input, output;
    object obj, nested;
    otag first, child;
    unsigned char data[40000];
    size_t used;
    int n, consumed;
    hd_receipt_set receipts, resumed;
    char claim[33], digest[65];
    memset(&input, 0, sizeof input);
    memset(&output, 0, sizeof output);
    memset(&obj, 0, sizeof obj);
    memset(&nested, 0, sizeof nested);
    memset(&first, 0, sizeof first);
    memset(&child, 0, sizeof child);
    memset(&receipts, 0, sizeof receipts);
    strcpy(input.name,"Nativeqa");
    input.gold = 8492;
    strcpy(obj.name,"Round 73 Testing Blade");
    strcpy(nested.name,"Round 73 Tiny Token");
    first.obj = &obj;
    child.obj = &nested;
    input.first_obj = &first;
    obj.first_obj = &child;
    n = write_crt_to_mem((char*)data, &input, 0);
    assert(n > 0 && n < (int)sizeof(data));
    memset(claim, 'a', 32); claim[32] = '\0';
    memset(digest, 'f', 64); digest[64] = '\0';
    assert(hd_receipt_add(&receipts, claim, digest) == 0);
    assert(hd_receipt_encode(data, sizeof(data), (size_t)n, &receipts, &used) == 0);
    consumed = read_crt_from_mem((char*)data, &output);
    assert(consumed == n); /* Real native loader ignores bytes after serialized items */
    assert(!strcmp(output.name,"Nativeqa"));
    assert(output.gold == 8492);
    assert(output.first_obj && !strcmp(output.first_obj->obj->name,"Round 73 Testing Blade"));
    assert(output.first_obj->obj->first_obj &&
           !strcmp(output.first_obj->obj->first_obj->obj->name,"Round 73 Tiny Token"));
    assert(hd_receipt_decode(data, used, (size_t)consumed, &resumed) == 0);
    assert(hd_receipt_lookup(&resumed, claim, digest) == 1);
#ifdef HD_WITH_ORIGINAL_COMPRESS
    {
        int packed = compress((char*)data, (char*)compressed, (int)used);
        int expanded;
        assert(packed > 0 && packed < 50000);
        expanded = uncompress((char*)compressed, (char*)unpacked, packed);
        assert(expanded == (int)used);
        assert(memcmp(unpacked, data, used) == 0);
        assert(hd_receipt_decode(unpacked, (size_t)expanded, (size_t)consumed, &resumed) == 0);
        puts("ROUND 73G: original compressed raw player stream roundtrip PASS");
    }
#endif
    free_objects(output.first_obj);
    puts("ROUND 73G: actual native files3.c nested inventory + receipt trailer PASS");
    return 0;
}
