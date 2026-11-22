/* Round 79F: immutable-snapshot Breath metadata for native atomic player store.
 * This is a FORMAT AND STATE CONTRACT, not a complete native store hook.
 * The 64-character digest fits an HDTR1 receipt payload without changing
 * the ELF32 creature layout or legacy player-save structure.
 */
#ifndef HD_BREATH_RECORD_H
#define HD_BREATH_RECORD_H

#include <stdint.h>

#define HD_BREATH_WIRE_HEX_LENGTH 64U

enum {
    HD_BREATH_OP_TRAVEL = 1,
    HD_BREATH_OP_RECOVER = 2
};

typedef struct hd_breath_record {
    char epoch[25];
    uint32_t revision;
    uint32_t last_recover;
    unsigned current;
} hd_breath_record;

/* Immutable output on malformed input. All return 0 success / -1 failure. */
int hd_breath_record_valid(const hd_breath_record *);
int hd_breath_record_new(hd_breath_record *, const char *epoch,
                          uint32_t now);
int hd_breath_record_encode(const hd_breath_record *, char out[65]);
int hd_breath_record_decode(const char *wire, hd_breath_record *);

/* Applies one successful wilderness step or one verified native regen tick.
 * destination_is_wilderness is 0/1 for travel. resting is 0/1 for recover.
 * A successful indoor move is a no-op, not a Breath debit.
 * Recover is only called from a verified native timer callback, NEVER from
 * the command loop; last_recover disallows duplicate same-second ticks.
 */
int hd_breath_record_step(const hd_breath_record *expected,
                          hd_breath_record *next, unsigned operation,
                          int destination_is_wilderness, int resting,
                          uint32_t now);
#endif
