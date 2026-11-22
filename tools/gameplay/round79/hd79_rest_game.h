/* Round79P: private native rest mode, separate from legacy social emotes.
 * No creature save/ELF32 structure additions and no mount effects.
 * Caller includes the normal native creature/cmd declarations first.
 */
#ifndef HD79_REST_GAME_H
#define HD79_REST_GAME_H
#include <stdint.h>
int hd79_rest_command(creature *player,cmd *command);
void hd79_rest_before_command(creature *player,const char *word);
void hd79_rest_forget(creature *player);
int hd79_rest_bonus_eligible(creature *player,uint32_t now,
                              uint32_t durable_last_recover);
#ifdef HD79_REST_TESTING
int hd79_rest_begin_at_for_test(creature *player,uint32_t now);
#endif
#endif
