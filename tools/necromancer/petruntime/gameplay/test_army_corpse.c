#define main legacy_main
#include "test_corpse.c"
#undef main
#include "hd_army_corpse.h"
#include <time.h>

static int ready, commits, rolls, rolls_in_attempt, roll_value, unique_roll, persisted;
static time_t clock_now = 1000;

time_t time(time_t *value)
{
    if (value) *value = clock_now;
    return clock_now;
}
int hd_necro_skeleton_is_pet(creature *pet) { (void)pet; return 0; }

int hd_army_raise_ready(creature *owner, const hd_army_corpse *corpse)
{
    assert(corpse->hp == 147 && corpse->mp == 51 && corpse->level == 12);
    assert(corpse->experience == 250 && !strcmp(corpse->name, "crypt rat"));
    return ready && owner->mpcur >= 8;
}
int hd_army_raise_commit(creature *owner, const hd_army_corpse *corpse)
{
    assert(owner->mpcur == 40 && corpse->experience == 250);
    assert(corpse->unique == persisted);
    assert(corpse->hp == (persisted ? 294U : 147U));
    assert(corpse->mp == (persisted ? 102U : 51U));
    assert(corpse->strength == (persisted ? 20U : 10U));
    assert(corpse->dexterity == (persisted ? 22U : 11U));
    assert(corpse->constitution == (persisted ? 24U : 12U));
    assert(corpse->intelligence == (persisted ? 26U : 13U));
    assert(corpse->piety == (persisted ? 28U : 14U));
    ++commits;
    return persisted;
}
int rand(void)
{
    int value = rolls_in_attempt++ ? unique_roll : roll_value;
    assert(value >= 1 && value <= 100);
    ++rolls;
    return (value - 1) * 10;
}

static void capture(creature *victim, room *where)
{
    dead(victim, where, "crypt rat", 147, 51);
    victim->experience = 250;
    victim->strength = 10;
    victim->dexterity = 11;
    victim->constitution = 12;
    victim->intelligence = 13;
    victim->piety = 14;
    victim->gold = 13;
    victim->first_obj = item("ruby", victim);
    assert(hd_corpse_capture(victim));
}

int main(void)
{
    creature owner = {0}, victim;
    room where = {0};
    cmd c;
    where.rom_num = 1;
    owner.type = PLAYER;
    owner.level = 12;
    owner.fd = 4;
    owner.mpcur = 40;
    owner.parent_rom = &where;

    capture(&victim, &where);
    command(&c, "raise corpse 1");
    hd_corpse_raise(&owner, &c);
    assert(!rolls && !commits);
    ready = 1;
    fail_gold = 1;
    hd_corpse_raise(&owner, &c);
    assert(!rolls && !commits && !where.first_obj);
    fail_gold = 0;

    /* Level 12 against level 12 gives 61%. One point above fails. */
    roll_value = 62;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 1 && !commits && !where.first_obj && owner.mpcur == 40);
    roll_value = 1;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 1 && !commits);
    command(&c, "loot corpse 1");
    hd_corpse_loot(&owner, &c);
    assert(count(&where) == 2);
    clear_room(&where);

    capture(&victim, &where);
    command(&c, "RC 2");
    clock_now += 119;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 1 && !commits && strstr(output, "ready in 1 second."));
    ++clock_now;
    roll_value = 61;
    unique_roll = 6;
    rolls_in_attempt = 0;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 3 && commits == 1 && !where.first_obj);
    hd_corpse_raise(&owner, &c);
    assert(rolls == 3 && commits == 1);
    command(&c, "loot corpse 2");
    hd_corpse_loot(&owner, &c);
    assert(count(&where) == 2);
    clear_room(&where);

    capture(&victim, &where);
    command(&c, "rc");
    clock_now += HD_ARMY_RAISE_COOLDOWN;
    roll_value = 61;
    unique_roll = 5;
    rolls_in_attempt = 0;
    persisted = 1;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 5 && commits == 2 && count(&where) == 2);
    hd_corpse_raise(&owner, &c);
    assert(rolls == 5 && commits == 2 && count(&where) == 2);
    clear_room(&where);
    assert(strstr(output, "unique undead crypt rat"));
    puts("PASS: shared cooldown, RC alias, unique roll boundary, and original loot");
    return 0;
}
