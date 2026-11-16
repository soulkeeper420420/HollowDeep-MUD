/* Round 73G private native player store; not enabled in production. */
#ifndef HD_PLAYER_STORE_H
#define HD_PLAYER_STORE_H
#include "mstruct.h"
#include "treasure_receipt.h"

/* All paths refer to the game's relative PLAYERPATH, never a caller URL. */
#define HD_STORE_FAILURE (-1)
#define HD_STORE_UNCERTAIN (-2) /* atomic rename happened; verify disk before retry */
#define HD_STORE_OK 0
#define HD_STORE_ALREADY_CLAIMED 1

int hd_store_load_player(const char *name, creature **out);
int hd_store_save_player(const char *name, creature *player);
/* For trusted native grants ONLY: staged contains the complete new inventory,
 * gold and normalized worn equipment. This does not mutate the live player.
 * Caller must re-read disk and reconcile before acknowledging ledger claim.
 */
int hd_store_save_claim(const char *name, creature *staged,
                        const char *claim_id, const char *digest);
int hd_store_read_claim(const char *name, const char *claim_id,
                        const char *digest); /* -1 invalid, 0 missing, 1 exact */
#endif
