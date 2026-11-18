#ifndef HD_CONJURE_H
#define HD_CONJURE_H

#include <stdint.h>

#define HD_CONJURE_COOLDOWN 300U
#define HD_CONJURE_LEVEL_CAP 60U
#define HD_CONJURE_XP_CAP 348100U

enum {
    HD_CJ_INIT, HD_CJ_SUMMON, HD_CJ_RECALL,
    HD_CJ_DISMISS, HD_CJ_DEATH, HD_CJ_XP,
    HD_CJ_VITALS, HD_CJ_RELEASE
};

typedef struct {
    const char *key, *name;
    unsigned unlock, hp, mp, hp_growth, mp_growth;
    unsigned strength, dexterity, constitution;
    unsigned intelligence, piety, proc;
} hd_conjure_template;

typedef struct {
    char epoch[25];
    uint32_t revision, last_cast, xp;
    unsigned species, active, hp, mp, level;
} hd_conjure_state;

const hd_conjure_template *hd_conjure_get(unsigned);
unsigned hd_conjure_hp(unsigned, unsigned);
unsigned hd_conjure_mp(unsigned, unsigned);
uint32_t hd_conjure_threshold(unsigned);
int hd_conjure_valid(const hd_conjure_state *);

int hd_conjure_step(hd_conjure_state *, unsigned,
                    unsigned, uint32_t, unsigned, unsigned);

unsigned hd_conjure_drain(unsigned, unsigned, unsigned,
                          unsigned, unsigned, uint32_t,
                          uint32_t *, unsigned *, unsigned *);

int hd_conjure_store_read(const char *, hd_conjure_state *);

int hd_conjure_store_apply(const char *,
                          const hd_conjure_state *,
                          unsigned, uint32_t,
                          unsigned, unsigned,
                          hd_conjure_state *);

#endif
