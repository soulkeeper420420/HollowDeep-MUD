/* Round 73G: trusted native inventory staging, atomic player-save receipt.
 * DOES NOT authorize guardians, maps, or player-chosen reward manifests.
 * Never attach to open chest until persistent kill/claim authority is proven.
 */
#include "hd_native_reward.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

#define HD_TOP_LEVEL_MAX 80U
#define HD_GOLD_GRANT_CAP 1000000L

static int hex_string(const char *s, unsigned n) {
    unsigned i;
    if (!s || s[n]) return 0;
    for (i = 0; i < n; ++i)
        if (!((s[i] >= '0' && s[i] <= '9') ||
              (s[i] >= 'a' && s[i] <= 'f'))) return 0;
    return 1;
}
static int safe_name(const char *s) {
    unsigned i;
    if (!s || s[0] < 'A' || s[0] > 'Z') return 0;
    for (i = 1; i < 15; ++i) {
        if (!s[i]) return i >= 2;
        if (!((s[i] >= 'A' && s[i] <= 'Z') ||
              (s[i] >= 'a' && s[i] <= 'z'))) return 0;
    }
    return 0;
}
static int valid_manifest(const creature *p, const hd_native_reward *m) {
    unsigned i,j;
    if (!p || !m || !safe_name(m->owner) ||
        strncmp(m->owner,p->name,sizeof m->owner) ||
        !hex_string(m->claim_id,32) || !hex_string(m->digest,64) ||
        m->count > HD_REWARD_LIMIT || m->gold < 0 ||
        m->gold > HD_GOLD_GRANT_CAP ||
        (m->count == 0 && m->gold == 0) ||
        p->gold < 0 || p->gold > LONG_MAX-m->gold)
        return 0;
    for (i=0; i<m->count; ++i) {
        const hd_reward_unit *u = &m->items[i];
        if (!hex_string(u->instance_id,32) || u->template_id < 1 ||
            u->template_id >= OMAX ||
            (u->kind != 'i' && u->kind != 'm') ||
            u->enchant_power != 0) return 0;
        for (j=0; j<i; ++j)
            if (!strcmp(u->instance_id,m->items[j].instance_id)) return 0;
    }
    return 1;
}
static void release_new(otag *first) {
    while (first) {
        otag *next=first->next_tag;
        free(first->obj);
        free(first);
        first=next;
    }
}
static int top_count(const creature *p, unsigned extra) {
    const otag *t=p->first_obj;
    unsigned count=extra;
    /* Detect chains exceeding the native count_inv() 80-entry cap. */
    while (t && count <= HD_TOP_LEVEL_MAX) {
        if (!t->obj) return -1;
        ++count;
        t=t->next_tag;
    }
    return t || count > HD_TOP_LEVEL_MAX ? -1 : 0;
}
int hd_native_reward_apply(creature *live, const hd_native_reward *manifest,
                           hd_reward_template_loader loader,
                           hd_reward_can_carry carry, void *context) {
    creature staged;
    otag *fresh=NULL, *last=NULL;
    unsigned i;
    int status, present;
    if (!valid_manifest(live,manifest) || !loader || !carry ||
        top_count(live,manifest->count)) return HD_REWARD_DENIED;
    /* Existing native player snapshot MUST exist and be parseable. Absence,
     * corruption or a mismatching digest always fails closed. */
    present=hd_store_read_claim(manifest->owner,manifest->claim_id,manifest->digest);
    if (present==1) return HD_REWARD_ALREADY;
    if (present<0) return HD_REWARD_DENIED;
    staged=*live; /* Preserve all native session fields without modifying live. */
    staged.gold=live->gold+manifest->gold;
    for (i=0; i<manifest->count; ++i) {
        object *obj=NULL;
        otag *tag;
        if (loader(manifest->items[i].template_id,&obj,context) || !obj) {
            free(obj); /* Callback may have allocated before reporting error. */
            goto denied;
        }
        /* Native template banks may contain serialized/stale pointers.
         * They are NEVER inherited into newly created player objects. */
        obj->first_obj=NULL;
        obj->parent_obj=NULL;
        obj->parent_rom=NULL;
        obj->parent_crt=&staged;
        if (!memchr(obj->name,'\0',sizeof obj->name) ||
            F_ISSET(obj,ONOTAK) || F_ISSET(obj,OSCENE) ||
            F_ISSET(obj,OTEMPP) || F_ISSET(obj,OWEARS) ||
            !carry(live,obj,context)) {
            free(obj);
            goto denied;
        }
        tag=(otag *)calloc(1,sizeof *tag);
        if (!tag) { free(obj); goto denied; }
        tag->obj=obj;
        if (last) last->next_tag=tag;
        else fresh=tag;
        last=tag;
    }
    if (last) last->next_tag=live->first_obj;
    staged.first_obj=fresh ? fresh:live->first_obj;
    status=hd_store_save_claim(manifest->owner,&staged,
                               manifest->claim_id,manifest->digest);
    /* Detach only the newly owned nodes before any temporary free. */
    if (last) last->next_tag=NULL;
    if (status==HD_STORE_UNCERTAIN) {
        /* Directory fsync did not finish. Even if a reread sees the receipt,
         * rename visibility does NOT prove crash durability. Do NOT mutate
         * live memory or acknowledge the ledger; freeze/reload the session. */
        release_new(fresh);
        return HD_REWARD_UNCERTAIN;
    }
    if (status==HD_STORE_OK) {
        /* Only an atomic save with confirmed directory fsync may commit live
         * memory, and only after independent persisted receipt verification. */
        present=hd_store_read_claim(manifest->owner,
                                    manifest->claim_id,manifest->digest);
        if (present != 1) {
            release_new(fresh);
            return HD_REWARD_UNCERTAIN;
        }
        live->gold=staged.gold;
        if (last) {
            last->next_tag=live->first_obj;
            live->first_obj=fresh;
            for (; fresh!=last; fresh=fresh->next_tag)
                fresh->obj->parent_crt=live;
            last->obj->parent_crt=live;
        }
        return HD_REWARD_APPLIED;
    }
    release_new(fresh);
    if (status==HD_STORE_ALREADY_CLAIMED)
        return HD_REWARD_ALREADY;
    return HD_REWARD_DENIED;
denied:
    release_new(fresh);
    return HD_REWARD_DENIED;
}
