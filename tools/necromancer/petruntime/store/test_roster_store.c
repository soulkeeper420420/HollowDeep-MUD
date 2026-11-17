#define main legacy_main
#include "test_pet_store.c"
#undef main
#include "hd_pet_roster.h"

int hd_roster_store_read(const char *, hd_pet_roster *);
int hd_roster_store_checkpoint(const char *, const hd_pet_roster *,
                               const hd_pet_roster *, hd_pet_roster *);

int hd_roster_store_raise(const char *, const hd_pet_roster *,
                          const hd_roster_pet *, creature *, uint32_t,
                          long *, hd_pet_roster *);

int main(int argc, char **argv)
{
    char *seed[] = {argv[0], "seed", NULL};
    char *raise[] = {argv[0], "raise", NULL};
    hd_pet_roster old, next, check;
    hd_pet_state legacy;
    creature *owner, *disk;
    hd_roster_pet summon = {0};
    long xp;
    size_t i;
    (void)argc;

    assert(legacy_main(2, seed) == 0);
    assert(legacy_main(2, raise) == 0);
    assert(hd_roster_store_read(name, &old) == HD_PET_OK);
    assert(old.revision == 2 && old.count == 1 && old.pets[0].hpcur == 147);
    next = old;
    next.pets[0].hpcur = 100;
    next.pets[0].stay = 1;
    setenv("HD_ATOMIC_FAIL", "before_rename", 1);
    assert(hd_roster_store_checkpoint(name, &old, &next, &check) == HD_PET_ERROR);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_pet_store_read(name, &legacy) == HD_PET_OK && legacy.hpcur == 147);
    assert(hd_roster_store_checkpoint(name, &old, &next, &check) == HD_PET_OK);
    assert(check.revision == 3 && check.pets[0].hpcur == 100 && check.pets[0].stay);
    assert(hd_pet_store_init(name, &legacy) == HD_PET_ERROR);
    assert(hd_roster_store_checkpoint(name, &old, &old, &next) == HD_PET_CONFLICT);

    assert(hd_store_load_player(name, &owner) == 0);
    owner->mpcur = 109;
    assert(hd_store_save_live_player(name, owner) == 0);
    free_crt(owner);
    native_player(109);
    assert(hd_store_read_claim(name, claim, digest) == 1);
    assert(hd_roster_store_read(name, &next) == HD_PET_OK);
    assert(next.revision == 3 && next.pets[0].hpcur == 100 && next.pets[0].stay);

    next.count = 0;
    setenv("HD_ATOMIC_FAIL", "after_rename", 1);
    assert(hd_roster_store_checkpoint(name, &check, &next, &old) == HD_PET_UNCERTAIN);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_roster_store_read(name, &next) == HD_PET_OK);
    assert(next.revision == 4 && next.count == 0 && next.next_id == 2);
    assert(hd_roster_store_checkpoint(name, &next, &check, &old) == HD_PET_ERROR);
    check.revision = next.revision;
    assert(hd_roster_store_checkpoint(name, &next, &check, &old) == HD_PET_ERROR);
    native_player(109);
    assert(hd_store_read_claim(name, claim, digest) == 1);
    puts("PASS: atomic roster migration, save preservation, failure recovery, and removal");
    assert(hd_store_load_player(name, &owner) == 0);
    owner->level = 1;
    owner->experience = 100;
    summon.level = 2;
    summon.room = 1;
    summon.hpmax = summon.hpcur = 42;
    summon.template_id = 123;
    summon.unique = 1;
    summon.hpmax = summon.hpcur = 84;
    summon.mpmax = summon.mpcur = 20;
    summon.strength = 20;
    summon.dexterity = 22;
    summon.constitution = 24;
    summon.intelligence = 26;
    summon.piety = 28;
    strcpy(summon.name, "crypt rat");
    setenv("HD_ATOMIC_FAIL", "before_rename", 1);
    assert(hd_roster_store_raise(name, &next, &summon, owner, 200, &xp, &check) == HD_PET_ERROR);
    unsetenv("HD_ATOMIC_FAIL");
    assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 0);
    native_player(109);
    for (i = 0; i < 3; ++i) {
        assert(hd_roster_store_raise(name, &next, &summon, owner, 200, &xp, &check) == HD_PET_OK);
        assert(check.count == i + 1 && check.pets[i].id == i + 2);
        assert(check.pets[i].template_id == summon.template_id && xp == 120 + 20 * (long)i);
        assert(hd_roster_store_raise(name, &next, &summon, owner, 200, &xp, &old) == HD_PET_CONFLICT);
        assert(hd_store_load_player(name, &disk) == 0);
        assert(disk->mpcur == owner->mpcur - 8 && disk->experience == xp);
        free_crt(owner);
        owner = disk;
        next = check;
        ++summon.template_id;
    }
    assert(hd_roster_store_raise(name, &next, &summon, owner, 200, &xp, &check) == HD_PET_ERROR);
    free_crt(owner);
    native_player(85);
    assert(hd_store_read_claim(name, claim, digest) == 1);
    assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 3);
    assert(old.pets[0].unique && !strcmp(old.pets[0].name, "crypt rat"));
    assert(old.pets[0].hpmax == 84 && old.pets[0].mpmax == 20 &&
           old.pets[0].strength == 20 && old.pets[0].dexterity == 22 &&
           old.pets[0].constitution == 24 && old.pets[0].intelligence == 26 &&
           old.pets[0].piety == 28);
    next = old;
    next.pets[0].unique = 0;
    assert(hd_roster_store_checkpoint(name, &old, &next, &check) == HD_PET_ERROR);
    next = old;
    ++next.pets[0].piety;
    assert(hd_roster_store_checkpoint(name, &old, &next, &check) == HD_PET_ERROR);
    next = old;
    --next.pets[0].hpcur;
    assert(hd_roster_store_checkpoint(name, &old, &next, &check) == HD_PET_OK);
    assert(hd_roster_store_read(name, &next) == HD_PET_OK && next.pets[0].unique &&
           next.pets[0].piety == 28 && next.pets[0].hpcur == 83);
    puts("PASS: unique identity and boosted stats survive native save and reload");
    puts("PASS: three durable summons, bounded XP, exact mana debit, stale retry and capacity");
    return 0;
}
