/* HollowDeep 73G: native reward staging, not wired to player commands. */
#ifndef HD_NATIVE_REWARD_H
#define HD_NATIVE_REWARD_H
#include "hd_player_store.h"

#define HD_REWARD_LIMIT 32
#define HD_REWARD_APPLIED 0
#define HD_REWARD_ALREADY 1
#define HD_REWARD_DENIED (-1)
#define HD_REWARD_UNCERTAIN (-2)

/* Produced ONLY by the trusted server-side DurableRewardCoordinator.
 * The caller must authenticate map ownership and exact guardian kills and
 * verify the manifest digest before constructing this fixed-size record.
 * This interface is not safe to expose as a player-controlled RPC or command.
 * Native enchantments require a separately audited effect mapping and are
 * explicitly unsupported in this foundation (fail closed).
 */
typedef struct {
    char instance_id[33];
    int template_id;
    char kind; /* 'i'=item, 'm'=material */
    int enchant_power; /* must be zero until mapping is implemented */
} hd_reward_unit;

typedef struct {
    char owner[80];
    char claim_id[33];
    char digest[65];
    unsigned count;
    long gold;
    hd_reward_unit items[HD_REWARD_LIMIT];
} hd_native_reward;

/* Return a newly allocated native template, or -1. No player input to loader. */
typedef int (*hd_reward_template_loader)(int, object **, void *);
/* Require native/game-specific carry/weight eligibility for EACH item. */
typedef int (*hd_reward_can_carry)(const creature *, const object *, void *);

/* Single game-thread call only. On successful atomic save, adds newly owned
 * nodes to live inventory; on failed save, live memory is unchanged. On an
 * uncertain result, a matching independently read receipt confirms commit.
 * Caller must BLOCK further saves/relogin if HD_REWARD_UNCERTAIN is returned.
 * No claim acknowledgments happen inside this function.
 */
int hd_native_reward_apply(creature *live, const hd_native_reward *manifest,
                           hd_reward_template_loader loader,
                           hd_reward_can_carry carry, void *context);
#endif
