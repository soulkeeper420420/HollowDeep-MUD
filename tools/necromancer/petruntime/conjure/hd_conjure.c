#include "hd_conjure.h"
#include <string.h>

static const hd_conjure_template companions[] = {
    {"wolf", "spectral wolf",
        1, 45, 20, 8, 3, 12, 17, 12, 8, 9, 0},
    {"scorpion", "venom scorpion",
        10, 55, 25, 9, 3, 14, 16, 14, 8, 8, 10},
    {"fire", "fire elemental",
        20, 50, 60, 7, 8, 10, 12, 12, 18, 11, 15},
    {"minotaur", "minotaur guardian",
        30, 100, 20, 15, 3, 18, 10, 18, 8, 10, 10},
    {"wraith", "shadow wraith",
        40, 65, 100, 8, 12, 10, 14, 12, 18, 18, 20},
    {"dragon", "ancient dragon",
        60, 125, 90, 16, 10, 18, 16, 18, 18, 16, 15}
};

static unsigned cj_min(unsigned a, unsigned b)
{
    return a < b ? a : b;
}

const hd_conjure_template *hd_conjure_get(unsigned id)
{
    return id >= 1 && id <= 6 ? &companions[id-1] : 0;
}

unsigned hd_conjure_hp(unsigned species, unsigned level)
{
    const hd_conjure_template *t = hd_conjure_get(species);
    return t && level && level <= 60 ?
        t->hp + (level-1)*t->hp_growth : 0;
}

unsigned hd_conjure_mp(unsigned species, unsigned level)
{
    const hd_conjure_template *t = hd_conjure_get(species);
    return t && level && level <= 60 ?
        t->mp + (level-1)*t->mp_growth : 0;
}

uint32_t hd_conjure_threshold(unsigned level)
{
    if (!level || level > 60) return UINT32_MAX;
    return 100U*(level-1)*(level-1);
}

int hd_conjure_valid(const hd_conjure_state *s)
{
    if (!s || s->active > 1 ||
        s->xp > HD_CONJURE_XP_CAP)
        return 0;

    if (!s->species)
        return !s->active && !s->hp && !s->mp &&
               !s->xp && !s->level;

    return hd_conjure_get(s->species) &&
        s->level >= 1 && s->level <= 60 &&
        s->xp >= hd_conjure_threshold(s->level) &&
        s->hp && s->hp <= hd_conjure_hp(s->species,s->level) &&
        s->mp <= hd_conjure_mp(s->species,s->level);
}

static int cj_ready(const hd_conjure_state *s, uint32_t now)
{
    return now && (!s->last_cast ||
        (now >= s->last_cast &&
         now-s->last_cast >= HD_CONJURE_COOLDOWN));
}

int hd_conjure_step(hd_conjure_state *s, unsigned action,
                    unsigned owner_level, uint32_t now,
                    unsigned a, unsigned b)
{
    hd_conjure_state n;
    const hd_conjure_template *t;
    unsigned oldhp, oldmp;

    if (!hd_conjure_valid(s) ||
        !owner_level || owner_level > 60)
        return -1;

    n = *s;

    switch (action) {
    case HD_CJ_SUMMON:
        t = hd_conjure_get(a);
        if (n.species || !t || owner_level < t->unlock ||
            !cj_ready(&n,now))
            return -1;

        n.species = a;
        n.active = 1;
        n.level = 1;
        n.hp = t->hp;
        n.mp = t->mp;
        n.last_cast = now;
        break;

    case HD_CJ_RECALL:
        t = hd_conjure_get(n.species);
        if (!t || n.active || !cj_ready(&n,now) ||
            owner_level < t->unlock || owner_level < n.level)
            return -1;
        n.active = 1;
        n.last_cast = now;
        break;

    case HD_CJ_DISMISS:
        if (!n.species || !n.active) return -1;
        n.active = 0;
        break;

    case HD_CJ_DEATH:
        if (!n.species || !n.active) return -1;
        n.species = n.active = n.level = 0;
        n.hp = n.mp = n.xp = 0;
        break;

    case HD_CJ_RELEASE:
        if (!n.species || n.active) return -1;
        n.species = n.level = n.hp = n.mp = n.xp = 0;
        break;

    case HD_CJ_XP:
        if (!n.species || !n.active ||
            !a || n.level > owner_level)
            return -1;

        n.xp += cj_min(a,HD_CONJURE_XP_CAP-n.xp);

        oldhp = hd_conjure_hp(n.species,n.level);
        oldmp = hd_conjure_mp(n.species,n.level);

        while (n.level < owner_level &&
               n.xp >= hd_conjure_threshold(n.level+1))
            ++n.level;

        n.hp += hd_conjure_hp(n.species,n.level)-oldhp;
        n.mp += hd_conjure_mp(n.species,n.level)-oldmp;
        break;

    case HD_CJ_VITALS:
        if (!n.species || !n.active) return -1;
        n.hp = a;
        n.mp = b;
        break;

    default:
        return -1;
    }

    if (!hd_conjure_valid(&n)) return -1;
    *s = n;
    return 0;
}

/* Shadow Wraith: 20% chance, 10% maximum target MP.
   Split the actual drain into two capped restoration pools. */
unsigned hd_conjure_drain(
    unsigned roll, unsigned enemy_mp, unsigned enemy_max,
    unsigned owner_missing, unsigned pet_missing,
    uint32_t now, uint32_t *last,
    unsigned *owner_gain, unsigned *pet_gain)
{
    unsigned drained;

    if (!last || !owner_gain || !pet_gain) return 0;
    *owner_gain = *pet_gain = 0;

    if (!roll || roll > 20 || !now ||
        (*last && (now < *last || now-*last < 3)))
        return 0;

    drained = cj_min(enemy_mp,enemy_max/10);

    if (!drained) return 0;

    *last = now;
    *owner_gain = cj_min(owner_missing,
                         drained/2 + drained%2);
    *pet_gain = cj_min(pet_missing,drained/2);
    return drained;
}
