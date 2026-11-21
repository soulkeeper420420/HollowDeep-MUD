/* Round 78E: isolated native ELF32 identity/receipt regression.
 * Never run from the production world. Requires empty disposable player/.
 */
#include "hd_player_store.h"
#include <assert.h>
#include <dirent.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

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

static void private_fixture_guard(int verifying_existing_save)
{
    const char *expected = getenv("HD_PRIVATE_WARLOCK_TEST_ROOT");
    static const char private_build[] = "/root/hollowdeep-dev/round78e-";
    static const char private_probe[] = "/tmp/hd-warlock-receipt-check-";
    char cwd[PATH_MAX];
    struct stat st;
    DIR *directory;
    struct dirent *entry;

    if (!expected || !getcwd(cwd, sizeof cwd) || strcmp(expected,cwd) ||
        (strncmp(cwd,private_build,sizeof(private_build)-1) &&
         strncmp(cwd,private_probe,sizeof(private_probe)-1))) {
        fputs("REFUSED: Not a private Round 78E fixture directory\n", stderr);
        exit(2);
    }
    if (lstat("player",&st) || !S_ISDIR(st.st_mode) ||
        st.st_uid!=geteuid() || (st.st_mode & 0077) != 0) {
        fputs("REFUSED: Unsafe private player fixture directory\n", stderr);
        exit(2);
    }
    if (verifying_existing_save) return;
    directory=opendir("player");
    if (!directory) exit(2);
    while ((entry=readdir(directory)) != NULL) {
        if (strcmp(entry->d_name,".") && strcmp(entry->d_name,"..")) {
            closedir(directory);
            fputs("REFUSED: Native test needs an empty player fixture\n", stderr);
            exit(2);
        }
    }
    closedir(directory);
}

int main(int argc, char **argv)
{
    private_fixture_guard(argc == 2);
    creature warlock, necromancer, mage, fighter, *reload = NULL;
    if (argc == 2) {
        assert(hd_store_load_player(argv[1], &reload) == 0);
        assert(reload && reload->class == MAGE);
        assert(hd_store_is_warlock(argv[1]) == 1);
        assert(hd_store_is_necromancer(argv[1]) == 0);
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
