# Hollowdeep server development kit

An editable extension kit for the **original Mordor 3.00** by Brett Vickers and Brooke Paul. This is the original native C engine, with compatibility adjustments and Hollowdeep exploration, progression, stance and staff commands. The browser client remains at https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/.

## What is included

- `manage.py`: checksum-verified source preparation, a 32-bit build, explicit extension synchronization, and a foreground development launcher.
- `extensions/hollowdeep.c`: character/training guidance and four persistent exploration Chronicles.
- `extensions/hollowdeep_stance.c`: persistent balanced, guarded and aggressive physical-combat stances.
- `extensions/hollowdeep_staff.c`: owner/admin/mod/implementor roles, announcements, timed mutes, kicks and a bounded audit.
- `extensions/hollowdeep_net.c`: per-connection Telnet and line-ending normalization for native and browser clients.
- `extensions/hollowdeep_build.c`, `hollowdeep_ranges.c`: assigned world-building ranges and role-based DM tools.
- `extensions/hollowdeep_bonus.c`: persistent timed monster XP/gold events with bounded multipliers.
- `extensions/hollowdeep_help.c`: command-table help, role-aware DM guide and native skill eligibility.
- `extensions/help.84` through `help.97`, plus repaired original pages: in-game help for every registered command.
- `tests/`: native extension behavior tests and source preparation checks.
- `bridge/` in the download: the Node.js WebSocket-to-Telnet bridge, including its dependency lockfile.
- Original copyright and disclaimer notices. The downloadable kit also includes the unmodified `Mordor_3.00.tar.gz` distribution.

The original ten classes, combat, spells, world and player-file format remain in Mordor. Atlas inspired the emphasis on class guidance, exploration, party tools and an accessible help library. This kit does not copy Atlas content or implement its remort classes, player housing or shop ownership.

## Requirements and verification

Use Linux with Python 3, Make and a **32-bit-capable GCC toolchain**. On Debian/Ubuntu this normally means `build-essential`, `gcc-multilib` and `libc6-dev-i386`. Ask a shared hosting provider to supply these; root access is not required by the toolkit itself. An x86 Linux host is the simplest target.

On a Debian/Ubuntu host you administer, install the prerequisites with:

```sh
sudo apt-get update
sudo apt-get install python3 build-essential gcc-multilib libc6-dev-i386
```

The original world files serialize native C structures. A normal 64-bit executable is incompatible with that data, so the build refuses to proceed without a working 32-bit compiler and runtime. Do not remove `-m32` to bypass this check.

The updated original engine compiles and links as an ELF32 executable. The extension, staff, stance, input and preparation checks run locally; 32-bit harnesses can also run through QEMU i386. The full updated ELF32 multiplayer test passed locally through QEMU, including private staff chat, command discovery, building, role revocation and restart persistence. New source features still require the guarded live update; these tests use disposable worlds. GitHub verification also runs the native checks.

Connection compatibility fixes handle CRLF and CR-NUL split across TCP reads, remove Telnet negotiation from player input, preserve prompts during negotiation-only reads, and keep password echo disabled during character creation. Preparation also corrects the original weather-array declaration and oversized lockout-message writes for modern compilers.

## Prepare, build and play locally

Extract the downloadable kit, open a terminal in `hollowdeep-server-kit`, then run:

```sh
python3 manage.py prepare --archive Mordor_3.00.tar.gz --destination ../hollowdeep-world --admin Realmkeeper
python3 manage.py build --work ../hollowdeep-world
python3 manage.py run --work ../hollowdeep-world --port 4040
```

If the compiler can link 32-bit programs but the host cannot execute them directly, install `qemu-user` and add `--runner /usr/bin/qemu-i386` to both `build` and `run`. This is optional; ordinary x86 Linux hosts with i386 execution support can use the commands above. A compiler installed outside the system paths can be selected with `build --cc /path/to/compiler-wrapper`.

Choose your own administrative character name in place of `Realmkeeper` (3–14 letters, initial capital). Preparation refuses to overwrite an existing destination. It preserves the original notices, imports the original world and source, excludes distributed player accounts and old executable files, and configures only your chosen administrative name. Source changes are recorded in `hollowdeep-compatibility.patch`.

Connect a MUD client to `127.0.0.1`, port `4040`, and create the configured administrator locally before permitting public connections. Native clients use Mordor's character login; browser ChatGPT sign-in does not grant game administrator powers.

If you have the source checkout rather than the downloadable bundle, fetch the pinned archive first:

```sh
python3 manage.py fetch --output Mordor_3.00.tar.gz
```

## Code the server and apply workshop changes

Open `/workshop` on the Hollowdeep site and choose **Load server kit**. Edit `extensions/hollowdeep.c` to change quest thresholds, class guidance or command behavior. Save a local draft and export a patch. Downloading the whole workshop JSON preserves original versions for future patches.

From the matching kit directory, apply your exported patch and sync the edited extensions into your prepared world:

```sh
git apply --check /path/to/hollowdeep-server.patch
git apply /path/to/hollowdeep-server.patch
python3 manage.py sync-extensions --work ../hollowdeep-world
python3 manage.py build --work ../hollowdeep-world
```

`sync-extensions` keeps backups of replaced files. It does not restart a running server. Save and quit test characters, stop the development process, and start the rebuilt engine again. If you edit files directly in `hollowdeep-world/src_3.00`, use `build` without synchronization; synchronization replaces the registered extension C/header files and associated help pages with the kit copies. It refuses older prepared checkouts that lack the new staff and stance hooks. Use the guarded native updater for the known live installation, or prepare a separate development checkout; keep the existing world and saves intact. Never prepare over a running world.

For broader engine changes, open the prepared `src_3.00` directory in your preferred code editor or import selected files into the browser workshop. Command registration is in `global.c`; player and room types are in `mstruct.h`; constants and class IDs are in `mtype.h`. `manage.py` documents each compatibility edit. When adding a new C file, register its handler and add its object to the prepared Makefile.

## Added native commands

| Command | Behavior |
| --- | --- |
| `hcommands [mobile\|social]` | Added commands and compact original-game guidance. |
| `spells` / `spell` | Alphabetical list of learned spells and current mana; casting requirements still apply. |
| `hbuild` / `hbuild mine` | Owner-assigned room ranges, room creation, names, descriptions and exits. |
| `hdm` | Scoped teleport, summon and HP/mana restoration powers. |
| `hbonus` | Show timed monster reward events; mods/implementors/admins/owners manage them within their role limits. |
| `hclass` / `hclass mage` | Guidance for your current class or a named original class. |
| `hclass progress` | Read-only original XP/gold thresholds and training eligibility checks. |
| `hquest` | List available, active and claimed Chronicles. |
| `hquest next` | Suggest a claimable, active or next available Chronicle. |
| `hquest accept first-steps` | Accept a chronicle. Other IDs: `mapmaker`, `apprentice`, `veteran`. |
| `hquest survey` | Record the character's actual current room once. |
| `hquest claim first-steps` | Claim the completed chronicle's badge. |
| `hprofile` | Show recorded places and earned badges. |
| `hprofile status` | Compact health/mana, class, level, XP, gold and Chronicle totals. |
| `hstance [balanced\|guarded\|aggressive]` | Inspect or choose a persistent physical-combat tradeoff. |
| `hstaff whoami` | Show your Hollowdeep role. |
| `hstaff grant <name> <role>` | Authorized owners/admins assign permitted staff roles. |
| `hstaff revoke <name>` / `list` / `audit` | Manage roles or inspect staff/audit records, subject to permissions. |
| `hmoderate announce\|mute\|unmute\|kick ...` | Staff moderation; see `help hmoderate` for arguments. |

First Steps needs 3 rooms; Mapmaker needs 10; Apprentice needs 3 rooms and level 3; Veteran needs 10 rooms and level 5. Earlier surveys count toward accepted chronicles. Rewards are cosmetic badges, not gold or experience. State is stored per character under `hollowdeep-data/`, separate from the original player structure. Keep quest IDs and bit positions stable after players begin earning them.

Stances use separate `.stance` files and change only ordinary physical hit thresholds. Their strength rises at levels 5 and 10; a 20-second timer beyond attack/spell cooldowns prevents swapping between attacks. Staff state uses an atomic `staff.db` sidecar with roles, timed mutes and the latest 64 audit records. Neither module changes the original serialized player structure. Staff roles do not grant native DM/caretaker privileges. Read the [player guide](https://github.com/soulkeeper420420/HollowDeep-MUD/blob/main/docs/PLAYER_GUIDE.md) and [staff guide](https://github.com/soulkeeper420420/HollowDeep-MUD/blob/main/docs/STAFF_GUIDE.md) for full syntax and behavior.

## Test and publish on a MUD host

```sh
python3 tests/test_prepare.py --archive Mordor_3.00.tar.gz
python3 tests/test_extensions.py --source ../hollowdeep-world/src_3.00
python3 tests/test_staff.py --source ../hollowdeep-world/src_3.00
python3 tests/test_stance.py --source ../hollowdeep-world/src_3.00
python3 tests/test_network.py --source ../hollowdeep-world/src_3.00
python3 tests/test_input.py --source ../hollowdeep-world/src_3.00
python3 tests/test_runtime_client.py
python3 tests/test_runtime.py --archive Mordor_3.00.tar.gz
```

The runtime smoke test creates and removes its own disposable world, builds the original engine, and connects two ordinary characters and a test founder. It checks character creation, world loading, chat, parties, progression guidance, staff permissions/muting, stances, Chronicle commands and persistence across a server restart. It accepts the same optional `--cc` and `--runner` settings as `build`. It never connects to an existing game or uses your real player saves.

Before public launch, test character creation/login, saving and reloading, movement, combat, training, party chat and every added chronicle with two client connections. Verify that the original world data reads correctly on the host. Back up `player/`, `hollowdeep-data/`, world files and local changes before replacing an existing installation.

Once the host allocates a public TCP port and your administrator exists:

```sh
python3 manage.py run --work ../hollowdeep-world --port 4040 --public
```

Use the host-assigned port in place of 4040. Run under the host's approved process supervisor for persistent service. The launcher binds loopback unless `--public` is supplied; it does not configure a firewall or provide hosting. Public-mode checks require your configured administrator's player file to exist.

The published browser interface also needs the Node.js 22 WebSocket bridge included in the kit's `bridge/` directory (the site's source calls it `server/`). Run `npm ci` in that directory. Configure `MORDOR_HOST=127.0.0.1`, the engine's `MORDOR_PORT`, the bridge HTTP `PORT`, and `ALLOWED_ORIGINS=https://hollowdeep-dungeon.soulkeeper420.chatgpt.site`. The preferred authentication mode uses an Ed25519 private key in the Sites secret `BRIDGE_SIGNING_KEY_PKCS8` and the matching public key in the bridge's `BRIDGE_PUBLIC_KEY_SPKI`. Start the bridge with `npm start` and provide trusted TLS so `/socket` is available over `wss://`. Configure Sites with `BRIDGE_URL`, `MUD_PUBLIC_HOST` and `MUD_PUBLIC_PORT`. Legacy `BRIDGE_SECRET` mode remains supported as an alternative, not alongside the key pair. Keep unsigned development access disabled for public hosting. Never put a private key, player save or password in the browser workshop.

The [server guide](https://github.com/soulkeeper420420/HollowDeep-MUD/blob/main/docs/SERVER_GUIDE.md) describes the separate native updater and TLS bridge installer for the existing Linode. The source [publishing guide](https://github.com/soulkeeper420420/HollowDeep-MUD/blob/main/docs/PUBLISHING.md) explains package generation and deployment status.

## License

Keep the original Mordor copyright and credits unchanged. Its authors permit free-of-charge use under the included COPYRIGHT terms; commercial use requires their permission. This kit grants no additional rights to their engine or to Atlas. The development commands do not publish the website or restart an existing supervised game. Deployment installers are separate tools with their own checks.

### Command parser boundary repair

The original parser could copy a sixth significant word into its five-token array. This caused Ubuntu to abort the candidate game on `hbuild name Hall of the Seven Lanterns`. Preparation now bounds both token-copy paths, terminates token/full-command strings, and bounds separator lookahead. The complete original text remains available to builder commands. Native builds keep `_FORTIFY_SOURCE=3` and stack protection enabled.

`tests/test_parser.py --source /path/to/prepared/src_3.00 --cc /path/to/gcc32` compiles the actual prepared parser with memory checks and exercises long room text, five/six-word boundaries, numeric selectors, articles and empty/long inputs. It is also mandatory in the generated native updater. The full multiplayer test covers room editing and persistence with those same build protections enabled.

## Help, skills and future progression

`help commands [page]` indexes the actual registered names and aliases. `help search <text> [page]` searches them; `help search` alone describes the original search skill. `dmcommands` (alias `dmhelp`) shows role and builder tools; `dmcommands native [page]` lists eligible original caretaker/DM commands. All protected commands still enforce their own restrictions.

`skills` shows class/level-eligible native abilities; `skills all` lists all 18 catalogued abilities. Known magic remains in `spells`. These are reference views, not a new skill-point system. Staff badges and `staffclan` derive from validated staff roles on every use.

Read [level and XP investigation](../docs/LEVELS_AND_EXPERIENCE.md) before changing progression. It documents the level-25 discontinuity, stat-table bounds, monk progression defect, and save-compatible migration requirements. [Future releases](../docs/FUTURE_RELEASES.md) and [quest-area designs](../docs/ATLAS_RESEARCH_AND_QUEST_DESIGN.md) are proposals, not activated gameplay.
