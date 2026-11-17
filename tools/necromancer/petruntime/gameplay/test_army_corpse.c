#define main legacy_main
#include "test_corpse.c"
#undef main
#include "hd_army_corpse.h"

static int ready, commits, rolls, roll_value, persisted;
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
    ++commits;
    return persisted;
}
int rand(void)
{
    assert(roll_value >= 1 && roll_value <= 100);
    ++rolls;
    return (roll_value - 1) * 10;
}

static void capture(creature *victim, room *where)
{
    dead(victim, where, "crypt rat", 147, 51);
    victim->experience = 250;
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
    command(&c, "raise corpse 2");
    roll_value = 61;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 2 && commits == 1 && !where.first_obj);
    hd_corpse_raise(&owner, &c);
    assert(rolls == 2 && commits == 1);
    command(&c, "loot corpse 2");
    hd_corpse_loot(&owner, &c);
    assert(count(&where) == 2);
    clear_room(&where);

    capture(&victim, &where);
    command(&c, "raise corpse 3");
    persisted = 1;
    hd_corpse_raise(&owner, &c);
    assert(rolls == 3 && commits == 2 && count(&where) == 2);
    hd_corpse_raise(&owner, &c);
    assert(rolls == 3 && commits == 2 && count(&where) == 2);
    clear_room(&where);
    puts("PASS: corpse metadata, one revival roll, and original loot ownership");
    return 0;
}
