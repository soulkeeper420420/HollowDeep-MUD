/* Round79N: standalone deterministic REST eligibility replay.
 * This is NOT native in-game verification. It protects the command
 * integration contract before touching the 32-bit Mordor runtime.
 */
#include "hd79_rest_session.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    hd79_rest_session state={0};
    hd79_rest_session copy;
    unsigned i;
    assert(!hd79_rest_session_eligible(&state,100,1));
    assert(hd79_rest_session_begin(NULL,100)==-1);
    assert(hd79_rest_session_begin(&state,0)==-1);

    hd79_rest_session_init(&state);
    assert(hd79_rest_session_begin(&state,100)==0);
    assert(state.active==1 && state.began_at==100);
    /* Rest command spam cannot reset start time or create instant bonus. */
    for(i=101;i<150;i++) {
        assert(hd79_rest_session_begin(&state,i)==0);
        assert(state.began_at==100);
        assert(!hd79_rest_session_eligible(&state,i,100));
    }
    assert(hd79_rest_session_eligible(&state,145,100)==1);
    puts("PASS: rest bonus requires 45 uninterrupted seconds and a durable tick");

    /* A new rest right before an already-due recovery may not upgrade
     * the usual +5 recovery to +15. */
    hd79_rest_session_interrupt(&state);
    assert(hd79_rest_session_begin(&state,180)==0);
    assert(!hd79_rest_session_eligible(&state,181,100));
    assert(!hd79_rest_session_eligible(&state,224,100));
    assert(hd79_rest_session_eligible(&state,225,180));
    puts("PASS: rest cannot be entered at the last second to gain +15");

    /* The recovery receipt's last_recover timestamp gates new awards. */
    assert(!hd79_rest_session_eligible(&state,225,225));
    assert(!hd79_rest_session_eligible(&state,269,225));
    assert(hd79_rest_session_eligible(&state,270,225));
    puts("PASS: unchanged last_recover receipt prevents command-spam refills");

    /* Gameplay interruptions must be called by native integration. */
    hd79_rest_session_interrupt(&state);  /* movement / attack / cast */
    assert(!hd79_rest_session_eligible(&state,400,200));
    assert(hd79_rest_session_begin(&state,401)==0);
    assert(!hd79_rest_session_eligible(&state,445,401));
    assert(hd79_rest_session_eligible(&state,446,401));
    puts("PASS: explicit interruption requires fresh uninterrupted rest");

    /* Caller reinitializes session on logout/death/reconnect. */
    copy=state;
    hd79_rest_session_init(&copy);
    assert(!hd79_rest_session_eligible(&copy,500,400));
    assert(!copy.active && !copy.began_at);
    puts("PASS: session initialization prevents logout/reconnect rest carryover");

    /* Clock rollback and timer absent/corrupt both fail closed. */
    assert(!hd79_rest_session_eligible(&state,10,2));
    assert(!hd79_rest_session_eligible(&state,470,0));
    assert(!hd79_rest_session_eligible(NULL,470,300));
    puts("PASS: clock rollback, missing receipt and missing session denied");

    puts("ROUND79N: ISOLATED EXPLICIT REST SESSION POLICY PASS");
    puts("NATIVE REST COMMAND, +15 PULSE AND DISCONNECT HOOKS: NOT YET WIRED");
    puts("PRODUCTION DEPLOYMENT: NONE");
    return 0;
}
