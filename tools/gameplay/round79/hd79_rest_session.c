/* Round79N: no I/O, no engine globals, no pointer-keyed state.
 * Enforces >=45 uninterrupted seconds in verified explicit rest mode
 * before any accelerated +15 Breath pulse can become eligible.
 * Normal +5 recovery remains independent of this state.
 */
#include "hd79_rest_session.h"

void hd79_rest_session_init(hd79_rest_session *state)
{
    if (!state) return;
    state->active=0;
    state->began_at=0;
}
int hd79_rest_session_begin(hd79_rest_session *state,uint32_t now)
{
    if (!state || !now) return -1;
    /* Repeating the rest command cannot reset or shortcut the timer. */
    if (state->active) return 0;
    state->active=1;
    state->began_at=now;
    return 0;
}
void hd79_rest_session_interrupt(hd79_rest_session *state)
{
    hd79_rest_session_init(state);
}
int hd79_rest_session_eligible(const hd79_rest_session *state,
                               uint32_t now,uint32_t last_recover)
{
    if (!state || state->active!=1 || !state->began_at ||
        !now || !last_recover || now<state->began_at ||
        now<=last_recover)
        return 0;
    if (now-state->began_at<HD79_REST_MIN_SECONDS ||
        now-last_recover<HD79_REST_MIN_SECONDS)
        return 0;
    return 1;
}
