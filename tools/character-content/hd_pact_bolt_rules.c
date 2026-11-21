/* Round 78F: deterministic resource and cooldown policy. Private-only. */
#ifndef HD_WARLOCK_PLAYTEST
#error "Pact Bolt rules are only available in private Warlock test builds"
#endif

#include "hd_pact_bolt_rules.h"

int hd_pact_bolt_check(const hd_pact_bolt_request *request,
                       hd_pact_bolt_result *result)
{
    hd_pact_bolt_result staged;
    long elapsed;
    int score;
    if (!request || !result ||
        request->level < 1 || request->level > 60 ||
        request->intelligence < 0 || request->intelligence > 35 ||
        request->mana < 0 || request->mana > 65535 ||
        request->pact_charges < 0 ||
        request->pact_charges > HD_PACT_BOLT_MAX_CHARGES ||
        (request->empower != 0 && request->empower != 1) ||
        request->now <= 0 || request->last_cast < 0)
        return HD_PACT_BOLT_INVALID;

    staged.damage=0;
    staged.mana_cost=0;
    staged.charges_consumed=0;
    staged.seconds_remaining=0;

    if (request->last_cast != 0) {
        if (request->now < request->last_cast) {
            staged.seconds_remaining=HD_PACT_BOLT_COOLDOWN_SECONDS;
            *result=staged;
            return HD_PACT_BOLT_COOLDOWN;
        }
        elapsed=request->now - request->last_cast;
        if (elapsed < HD_PACT_BOLT_COOLDOWN_SECONDS) {
            staged.seconds_remaining=HD_PACT_BOLT_COOLDOWN_SECONDS-elapsed;
            *result=staged;
            return HD_PACT_BOLT_COOLDOWN;
        }
    }
    if (request->mana < HD_PACT_BOLT_MP_COST)
        return HD_PACT_BOLT_NO_MANA;
    if (request->empower && request->pact_charges == 0)
        return HD_PACT_BOLT_NO_CHARGE;

    /* Playtest values, not the final tuned damage model. */
    score = 5 + request->level / 2 + request->intelligence / 3;
    if (score > 50)
        score = 50;
    staged.damage = request->empower ? 2 * score : score;
    staged.mana_cost = HD_PACT_BOLT_MP_COST;
    staged.charges_consumed = request->empower;
    *result=staged;
    return HD_PACT_BOLT_OK;
}
