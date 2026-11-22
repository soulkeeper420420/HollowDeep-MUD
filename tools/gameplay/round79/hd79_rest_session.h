/* Round79N: PRIVATE, engine-independent resting session eligibility.
 * A rest session is NOT a player-save field, mount, or persistent pet.
 * The integrating native engine must call begin only on an eligible
 * explicit rest command; interrupt on activity, combat, relocation,
 * logout, death and disconnection; and init on each new login.
 * This file cannot itself award or persist Breath.
 */
#ifndef HD79_REST_SESSION_H
#define HD79_REST_SESSION_H
#include <stdint.h>

#define HD79_REST_MIN_SECONDS 45U
typedef struct hd79_rest_session {
    uint32_t began_at;
    unsigned char active;
} hd79_rest_session;

void hd79_rest_session_init(hd79_rest_session *state);
int hd79_rest_session_begin(hd79_rest_session *state, uint32_t now);
void hd79_rest_session_interrupt(hd79_rest_session *state);
int hd79_rest_session_eligible(const hd79_rest_session *state,
                               uint32_t now,uint32_t last_recover);
#endif
