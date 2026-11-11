"""Patch only a newly copied Round 11K private stage."""
import sys
from pathlib import Path


def replace(path, old, new):
    source = path.read_text()
    if source.count(old) != 1:
        raise SystemExit(f"Expected one patch anchor in {path.name}: {old!r}")
    path.write_text(source.replace(old, new))


stage = Path(sys.argv[1]).resolve(strict=True)
if (stage.parent != Path("/root/hollowdeep-dev/guild-social-batch1") or
        not stage.name.startswith("round11-equip-11n-")):
    raise SystemExit("Round 11N requires a disposable stage")

funds = stage / "src/round9_test_funds.c"
replace(funds, "#include <stdio.h>", """#include <stdio.h>
#include <stdlib.h>
extern int add_obj_crt(object *, creature *);""")
replace(funds, "    if (player->gold != 0) {", """    if (command->num == 2 && !strcmp(command->str[1], "fixture")) {
        object *fixture = calloc(1, sizeof(*fixture));
        if (!fixture)
            return 0;
        strcpy(fixture->name, "Round Eleven Blade");
        strcpy(fixture->key[0], "r11blade");
        fixture->type = SHARP;
        fixture->wearflag = WIELD;
        fixture->weight = 1;
        fixture->shotsmax = fixture->shotscur = 10;
        fixture->ndice = fixture->sdice = 1;
        add_obj_crt(fixture, player);
        print(player->fd, "Round 11 fixture granted.\\n");
        return 0;
    }
    if (player->gold != 0) {""")

social = stage / "src/hollowdeep_social.c"
replace(social, "            if (!save_guilds(s)) {", """#ifndef HD_ROUND9_ISOLATED_FUNDS
#error "Round 11N fault hooks require an isolated build"
#endif
            if (unlink("/hollowdeep-data/round11n-ledger-fail") == 0 ||
                !save_guilds(s)) {""")
replace(social, "                if (hd_guild_save_equipped(player) < 0)",
        """                if (unlink("/hollowdeep-data/round11n-character-fail") == 0 ||
                    hd_guild_save_equipped(player) < 0)""")

runner = stage / "runner.py"
replace(runner, '    created = command(a, "clan create Nightfall")', '''    fixture = command(a, "r9fund fixture")
    check("Native fixture granted", "fixture granted" in fixture.lower(), fixture)
    wield = command(a, "wield r11blade")
    check("Native weapon wielded before guild founding", "you wield" in wield.lower(), wield)
    carried = command(a, "inventory")
    check("Wielded fixture leaves inventory", "Round Eleven Blade" not in carried, carried)
    founder_path = ROOT / "player" / name_a
    command(a, "save")
    before_founding = founder_path.read_bytes()
    ledger_path = ROOT / "hollowdeep-data/player-guilds.v1"
    ledger_before = ledger_path.read_bytes() if ledger_path.exists() else None
    (ledger_path.parent / "round11n-ledger-fail").touch()
    rejected = command(a, "clan create Nightfall")
    check("Injected ledger failure reported", "Guild storage failed" in rejected, rejected)
    check("Ledger unchanged on injected failure",
          (ledger_path.read_bytes() if ledger_path.exists() else None) == ledger_before)
    retained = command(a, "inventory")
    check("Deed retained on ledger failure", "Clan Deed" in retained, retained)
    created = command(a, "clan create Nightfall")
    founding_save = founder_path.read_bytes()
    check("Guild founding replaces the native save",
          founding_save != before_founding and "character save failed" not in created.lower())''')
replace(runner, '    created_c = command(c, "clan create Dawnwatch")', '''    stale_path = ROOT / "player" / name_c
    command(c, "save")
    stale_save = stale_path.read_bytes()
    (ledger_path.parent / "round11n-character-fail").touch()
    created_c = command(c, "clan create Dawnwatch")
    check("Injected post-ledger character failure reported",
          "character save failed" in created_c.lower(), created_c)
    check("Native character save unchanged after injected failure",
          stale_path.read_bytes() == stale_save)''')
replace(runner, '    PORT = 4042', '''    # Replay precisely the two transaction-boundary saves. The graceful
    # disconnect saves above must not mask a founding or reconciliation defect.
    founder_path.write_bytes(founding_save)
    stale_path.write_bytes(stale_save)
    PORT = 4042''')
replace(runner, '    guild_info = command(a, "clan info Nightfall")', '''    recovered = command(a, "inventory")
    check("Exactly one founding-save fixture recovered in inventory",
          recovered.count("Round Eleven Blade") == 1, recovered)
    wield_again = command(a, "wield r11blade")
    check("Recovered fixture wields after native restart",
          "you wield" in wield_again.lower(), wield_again)
    guild_info = command(a, "clan info Nightfall")''')
replace(runner, '    original_registry = registry.read_bytes()', '''    # The founding snapshot starts the leader at the registry.
    square = command(a, "east")
    if "square" not in square.lower():
        raise RuntimeError("Founding snapshot leader did not reach the public square")
    original_registry = registry.read_bytes()''')
