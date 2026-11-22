/* Round 79H: native atomic Breath receipt storage API (private gate only).
 * Source is included by hd_player_store.c under BREATH_STORE_PLAYTEST=1.
 * No world, player-struct ABI, Conjure roster or mount changes.
 */
#ifndef HD_BREATH_STORE_H
#define HD_BREATH_STORE_H
#include "hd_breath_record.h"
#include <stdint.h>

#define HD_BREATH_STORE_OK 0
#define HD_BREATH_STORE_FAILURE (-1)
#define HD_BREATH_STORE_ABSENT 1
#define HD_BREATH_STORE_CONFLICT 2
#define HD_BREATH_STORE_UNCERTAIN 3

/* Missing Breath records are initialized explicitly and only once;
 * routine save_ply and reconnect NEVER reset a depleted Breath record.
 * If snapshot outcome is UNCERTAIN, re-read before allowing another
 * operation. Expected revision/epoch is compared under the player lock.
 */
int hd_breath_store_read(const char *name,hd_breath_record *out);
int hd_breath_store_init(const char *name,uint32_t now,hd_breath_record *out);
int hd_breath_store_step(const char *name,
    const hd_breath_record *expected,unsigned action,
    int destination_is_wilderness,int resting,uint32_t now,
    hd_breath_record *out);
#endif
