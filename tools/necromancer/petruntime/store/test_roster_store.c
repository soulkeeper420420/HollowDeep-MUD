#define main legacy_main
#define hd_necro_skeleton_on_free legacy_free_hook
#define del_active legacy_del_active
#include "test_pet_store.c"
#undef main
#undef hd_necro_skeleton_on_free
#undef del_active
#include "hd_pet_roster.h"
#include "hd_army_restore.h"
#include "hd_army_corpse.h"
#include "hd_necro_skeleton.h"

void hd_necro_skeleton_death(creature *);
int hd_army_pet_command(creature *, cmd *);
static creature target;
static int enemy;
creature *find_crt(creature *viewer, ctag *list, char *query, int number)
{
    (void)viewer;
    (void)list;
    return number == 1 && !strcmp(query, "trialghoul") ? &target : NULL;
}
int is_enm_crt(char *name, creature *pet) { (void)name; return enemy && pet == &target; }
void add_enm_dmg(char *name, creature *pet, int damage)
{ (void)name; assert(pet == &target && damage > 0); }

static void pet_order(creature *owner, const char *text)
{
    cmd command = {0};
    strcpy(command.fullstr, text);
    hd_army_pet_command(owner, &command);
}
void print(int fd, char *format, ...) { (void)fd; (void)format; }
void del_active(creature *pet) { (void)pet; }
void add_crt_rom(creature *pet, room *where, int announce)
{ (void)announce; assert(!pet->parent_rom); pet->parent_rom = where; pet->rom_num = where->rom_num; }
void del_crt_rom(creature *pet, room *where)
{ assert(pet->parent_rom == where); pet->parent_rom = NULL; pet->rom_num = 0; }

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
    if (argc == 2 && !strcmp(argv[1], "restore-unique")) {
        creature *pets[HD_ROSTER_CAP] = {0};
        assert(hd_roster_store_read(name, &old) == HD_PET_OK);
        assert(hd_army_restore(&old, pets) == 0);
        assert(old.count == 3 && !pets[3]);
        assert(!strcmp(pets[0]->name, "crypt rat") &&
               strstr(pets[0]->description, "unique"));
        assert(pets[0]->type == MONSTER && pets[0]->fd == -1 &&
               !pets[0]->parent_rom && !pets[0]->experience && !pets[0]->gold);
        assert(pets[0]->hpmax == 84 && pets[0]->hpcur == 83 &&
               pets[0]->mpmax == 20 && pets[0]->mpcur == 20);
        assert(pets[0]->strength == 20 && pets[0]->dexterity == 22 &&
               pets[0]->constitution == 24 && pets[0]->intelligence == 26 &&
               pets[0]->piety == 28);
        for (i = 0; i < old.count; ++i)
            free(pets[i]);
        {
            room before = {0}, after = {0};
            creature *first;
            before.rom_num = 1;
            after.rom_num = 2;
            assert(hd_store_load_player(name, &owner) == 0);
            owner->parent_rom = &before;
            hd_necro_skeleton_reconnect(owner);
            first = hd_necro_skeleton_probe(owner);
            assert(first && first->parent_rom == &before && first->hpcur == 83);
            assert(hd_necro_skeleton_is_pet(first));
            pet_order(owner, "pets");
            pet_order(owner, "pet stay 2");
            assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.pets[0].stay);
            target.type = MONSTER;
            target.parent_rom = &before;
            target.hpcur = 12;
            pet_order(owner, "pet attack trialghoul");
            assert(target.hpcur == 12);
            enemy = 1;
            pet_order(owner, "pet attack trialghoul");
            assert(target.hpcur < 12 && target.hpcur >= 1);
            owner->parent_rom = &after;
            owner->rom_num = 2;
            hd_necro_skeleton_follow(owner, &before, &after);
            assert(first->parent_rom == &before);
            pet_order(owner, "pet follow 2");
            assert(first->parent_rom == &after);
            hd_necro_skeleton_death(first);
            del_crt_rom(first, &after);
            free_crt(first);
            hd_necro_skeleton_logout(owner);
            assert(!hd_necro_skeleton_probe(owner));
            free_crt(owner);
        }
        puts("PASS: fresh process reconstructed three native pets from saved roster");
        return 0;
    }

    if (argc == 2 && !strcmp(argv[1], "after-death")) {
        room start = {0};
        hd_army_corpse corpse = {0};
        int mana;
        long experience;
        assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 2);
        assert(old.pets[0].id == 3 && old.pets[1].id == 4);
        assert(old.pets[0].room == 2 && old.pets[1].room == 2);
        assert(hd_store_load_player(name, &owner) == 0);
        start.rom_num = owner->rom_num;
        owner->parent_rom = &start;
        hd_necro_skeleton_reconnect(owner);
        assert(hd_necro_skeleton_probe(owner));
        strcpy(corpse.name, "cave ghoul");
        corpse.level = 3;
        corpse.hp = 50;
        corpse.mp = 10;
        corpse.experience = 200;
        corpse.strength = 20;
        corpse.unique = 1;
        mana = owner->mpcur;
        experience = owner->experience;
        assert(hd_army_raise_commit(owner, &corpse));
        assert(owner->mpcur == mana - 8 && owner->experience == experience + 20);
        assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 3);
        assert(old.pets[2].id == 5 && old.pets[2].unique && old.pets[2].strength == 20 &&
               !strcmp(old.pets[2].name, "cave ghoul"));
        assert(!hd_army_raise_ready(owner, &corpse));
        pet_order(owner, "pet dismiss 4294967296");
        assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 3);
        pet_order(owner, "pet dismiss 3");
        assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 2 &&
               old.pets[0].id == 4 && old.pets[1].id == 5);
        pet_order(owner, "pet dismiss all");
        assert(hd_roster_store_read(name, &old) == HD_PET_OK && old.count == 0 &&
               old.next_id == 6);
        puts("PASS: pet status, stay, follow, combat assist, and durable dismissal");
        hd_necro_skeleton_logout(owner);
        free_crt(owner);
        puts("PASS: fresh login restores survivors and excludes the dead pet");
        return 0;
    }
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
    phase(argv[0], "restore-unique");
    phase(argv[0], "after-death");
    puts("PASS: unique identity and boosted stats survive native save and reload");
    puts("PASS: three durable summons, bounded XP, exact mana debit, stale retry and capacity");
    return 0;
}
