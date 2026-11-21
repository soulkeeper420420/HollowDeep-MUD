/* Round 78F: side-effect-free Pact Bolt playtest rules.
 * Does not mutate native player, creature, inventory, or save ABI.
 * This API evaluates only resource/cooldown math; native target and
 * combat bookkeeping MUST be verified before gameplay integration.
 */
#ifndef HD_WARLOCK_PACT_BOLT_RULES_H
#define HD_WARLOCK_PACT_BOLT_RULES_H

#define HD_PACT_BOLT_MP_COST 6
#define HD_PACT_BOLT_COOLDOWN_SECONDS 8L
#define HD_PACT_BOLT_MAX_CHARGES 3

enum hd_pact_bolt_status {
    HD_PACT_BOLT_OK = 0,
    HD_PACT_BOLT_INVALID = -1,
    HD_PACT_BOLT_NO_MANA = -2,
    HD_PACT_BOLT_COOLDOWN = -3,
    HD_PACT_BOLT_NO_CHARGE = -4
};

typedef struct hd_pact_bolt_request {
    int level;
    int intelligence;
    int mana;
    int pact_charges;
    int empower;
    long now;
    long last_cast;
} hd_pact_bolt_request;

typedef struct hd_pact_bolt_result {
    int damage;
    int mana_cost;
    int charges_consumed;
    long seconds_remaining;
} hd_pact_bolt_result;

int hd_pact_bolt_check(const hd_pact_bolt_request *request,
                       hd_pact_bolt_result *result);
#endif
