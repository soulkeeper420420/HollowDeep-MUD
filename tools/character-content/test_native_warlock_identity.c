/* Round 78E: isolated native ELF32 identity/receipt regression.
 * Never run from the production world. Requires empty disposable player/.
 */
#include "hd_player_store.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WARLOCK_CLAIM "ffffffffffffffffffffffffffffff78"
#define WARLOCK_DIGEST "a74d000000000000000000000000000000000000000000000000000000000001"

void merror(const char *reason, int severity)
{
    fprintf(stderr, "PRIVATE TEST ERROR: %s (%d)\n", reason, severity);
    abort();
}

static void make_player(creature *p, const char *name)
{
    memset(p, 0, sizeof(*p));
    assert(strlen(name) < sizeof p->name);
    strcpy(p->name, name);
    strcpy(p->password, "Fixturepass");
    p->type = PLAYER;
    p->class = MAGE;
    p->race = HUMAN;
    p->level = 1;
    p->rom_num = 1;
    p->fd = -1;
    p->hpcur = p->hpmax = 100;
    p->mpcur = p->mpmax = 50;
    p->strength = p->dexterity = p->constitution = 12;
    p->intelligence = p->piety = 16;
}

int main(int argc, char **argv)
{
    creature warlock, necromancer, mage, fighter, *reload = NULL;
    if (argc == 2) {
        assert(hd_store_load_player(argv[1], &reload) == 0);
        assert(reload && reload->class == MAGE);
        assert(hd_store_is_warlock(argv[1]) == 1);
        assert(hd_store_is_necromancer(argv[1]) == 0);
        assert(hd_store_read_claim(argv[1], WARLOCK_CLAIM, WARLOCK_DIGEST) == 1);
        free(reload);
        puts("PASS: Socket-created Warlock has verified durable identity");
        return 0;
    }
    assert(argc == 1);
    make_player(&warlock, "Hdwarqa");
    make_player(&necromancer, "Hdnecroqa");
    make_player(&mage, "Hdmageqa");
    make_player(&fighter, "Hdfightqa");
    fighter.class = FIGHTER;
    assert(hd_store_create_warlock(fighter.name, &fighter) != HD_STORE_OK);
    assert(hd_store_is_warlock(fighter.name) == 0);
    puts("PASS: Wrong native base class cannot create Warlock identity");

    assert(hd_store_create_warlock(warlock.name, &warlock) == HD_STORE_OK);
    assert(hd_store_is_warlock(warlock.name) == 1);
    assert(hd_store_is_necromancer(warlock.name) == 0);
    assert(hd_store_verified_remorts(warlock.name) == 0);
    assert(hd_store_read_claim(warlock.name, WARLOCK_CLAIM, WARLOCK_DIGEST) == 1);
    assert(hd_store_create_warlock(warlock.name, &warlock) != HD_STORE_OK);
    puts("PASS: Warlock first atomic save with separate native identity");

    assert(hd_store_save_player(warlock.name, &warlock) == HD_STORE_OK);
    assert(hd_store_is_warlock(warlock.name) == 1);
    assert(hd_store_load_player(warlock.name, &reload) == 0);
    assert(reload && reload->class == MAGE && reload->race == HUMAN);
    assert(reload->hpcur == warlock.hpcur && reload->mpcur == warlock.mpcur);
    free(reload);
    puts("PASS: Ordinary save/load preserves Warlock identity and stats");

    assert(hd_store_create_player(mage.name, &mage) == HD_STORE_OK);
    assert(hd_store_is_warlock(mage.name) == 0);
    assert(hd_store_is_necromancer(mage.name) == 0);
    assert(hd_store_save_claim(mage.name, &mage, WARLOCK_CLAIM, WARLOCK_DIGEST)
           != HD_STORE_OK);
    assert(hd_store_is_warlock(mage.name) == 0);
    puts("PASS: Ordinary Mage cannot gain reserved Warlock identity");

    assert(hd_store_create_necromancer(necromancer.name, &necromancer)
           == HD_STORE_OK);
    assert(hd_store_is_necromancer(necromancer.name) == 1);
    assert(hd_store_is_warlock(necromancer.name) == 0);
    assert(hd_store_save_claim(necromancer.name, &necromancer,
                               WARLOCK_CLAIM, WARLOCK_DIGEST) != HD_STORE_OK);
    assert(hd_store_is_necromancer(necromancer.name) == 1);
    puts("PASS: Existing Necromancer identity isolated from Warlock");

    warlock.class = FIGHTER;
    assert(hd_store_save_player(warlock.name, &warlock) == HD_STORE_OK);
    assert(hd_store_is_warlock(warlock.name) == 0);
    assert(hd_store_is_necromancer(warlock.name) == 0);
    puts("PASS: Receipt alone does not bypass native Mage identity guard");

    puts("ROUND 78E: NATIVE ATOMIC WARLOCK IDENTITY TEST PASS");
    return 0;
}
