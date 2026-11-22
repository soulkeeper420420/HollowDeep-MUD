# HollowDeep Mounts and Wilderness Breath — Round 79G

Status: **proposed mount system and pure-rule staging only**. The existing
ANSI creation choice and HP/MP status prompt were validated in private native
gameplay. Native Breath movement depletion/persistence and all mounts remain
unimplemented. No production deployment or service restart is authorized.

## Product goal

Breath is **travel stamina**, designed to make exploring a large overland
wilderness a meaningful activity and to give mounts a mechanical purpose.

- Traveling **on foot** spends the player's own Breath (100 maximum,
  baseline two points per successful wilderness move).
- Traveling **on a mount** spends that mount's own **Endurance**, not the
  player's Breath. Mounts do NOT provide free movement, and mounting/dismounting
  must never reset either resource. Player Breath recovery follows the native
  regeneration clock, not individual movement commands.
- The player HUD remains HP / MP / Breath. When mounted, include the mount's
  name and Endurance as a second readable status (ANSI optional). Do not
  silently replace the player Breath gauge with the mount's Endurance.
- A player can own multiple mounts eventually, but only **one mounted/active**
  at any time. The mount system is distinct from permanent Conjure companions,
  temporary undead pets, controlled monsters, and character class.
- Mount ownership must be bound to the player's durable character epoch.
  Mount identity, equipment/progression (future), active state, and Endurance
  require atomic, restart-safe persistence; never rely only on the map-session
  state or in-memory player pointers.
- Wilderness means a **validated tile in wilderness.map**, not just any
  room ID >= 10000 or a displayed map glyph. Native exit/door checks, room
  limits, secret exits, teleport constraints and instance restrictions still
  apply. A flying mount does not teleport or ignore exit permissions.

## First-playtest mounts (balance values are provisional)

| Mount | Endurance cap | Base cost per wilderness step | Terrain role |
|---|---:|---:|---|
| Horse | 120 | 1 | Roads and plains; forest slower |
| Warhorse | 140 | 1 | Roads, plains, forest, swamps and ruins |
| Dire wolf | 130 | 1 | Forest, plains, mountains, swamps and ruins |
| Nightmare | 160 | 1 | All land terrain |
| Griffin | 175 | 2 | Can traverse marked rivers; flying travel |
| Dark dragon | 220 | 1 | All mapped terrain; elite flying travel |

Native wilderness.map terrain symbols:
F forest, . plains, ^ mountain, S swamp, ~ river, = road, # ruins.

Forest/swamp/ruins and similar rough terrain can add a small movement
cost depending on the species. Unsupported terrain denies mounted movement
rather than silently moving the mount. Native exits remain authoritative.

**These numbers and species unlocks are proposals, not live balance.** A
horse can be an early vendor/quest mount. Griffin and dark dragon should
be late-game quest rewards with requirements and controlled availability,
not instant free summons. Define pricing, trading, PvP use, flight and
combat interaction in separate milestones before implementation.

## Initial commands (subject to native table collision audit)

- mount list — owned mounts and their status
- mount <name|id> — ride an eligible owned mount in the current location
- dismount — return to foot travel safely
- mount status — current mount, Endurance and terrain capabilities
- stable <name|id> and retrieve <name|id> — interact with a **verified**
  stable location; never summon through locked gates or remote instances
- call mount <name|id> — only where the world rules explicitly permit it
- help mounts / help breath — explain resource and terrain rules

Do not add these commands until checking exact native command collisions,
selector parser rules, GM permissions and load/save semantics.

## Exhaustion, recovery and anti-exploits

- Check resource and terrain BEFORE a wilderness move, and debit exactly
  once AFTER the engine verifies a successful room change. Failed movement,
  blocked exits, inventory commands, look, map redraw and teleport never
  charge Breath or mount Endurance.
- If the active mount has insufficient Endurance, deny further wilderness
  travel on that mount. Dismounting must not refill the mount. The player
  may continue on foot if player Breath permits.
- At 0 Breath/Endurance, always allow a verified move to an ordinary
  non-wilderness safe room. Allow non-cost recovery in wilderness via a
  native timed tick, so players cannot be trapped indefinitely.
- Each resource regenerates only on verified native timer ticks (rest can
  accelerate recovery). Never regenerate by repeatedly typing a command,
  relogging, changing mounts, dismissing/recalling pets or cycling areas.
- Recovery must have a durable last-tick contract and revisioned, locked
  state update. Native atomic failures should fail closed without charging
  once on failed movement or granting unlimited free successful moves.
- Mounts must remain separate from the existing PBRWAT water-breathing
  spell flag; Breath is NOT oxygen.

## Gameplay acceptance gates before claiming playable

1. Private source audit of the remaining native atomic Breath save report
   and verified wilderness exit-selection/commit path.
2. Finish persistent **player Breath** receipt first (epoch-bound, strictly
   revisioned, rollback-safe). Validate creation, save, reconnect, restart
   and fail-injection without changing the legacy creature binary ABI.
3. Add durable mount roster/Endurance state using the same atomic player
   save contract; preserve pet roster, Necromancer and Conjure receipts.
4. Native movement preview, successful debit and recovery; test foot and
   mounted traversal per terrain, stale revision, double charge, safe
   retreat, inaccessible rooms and invalid ownership.
5. Native ELF32 compile and isolated real socket gameplay. Validate exact
   ANSI/plain HUD, one mount slot, foot-to-mount switching, relog, stable,
   and Mage/Necromancer/Warlock creation and existing Conjure compatibility.
6. Publish tested source and public-facing guides; keep private logs,
   world snapshots and credentials out of GitHub. No live world edits or
   service restart without separate explicit approval.

## Round 79G staged rule prototypes

The native-independent hd_mount_travel.h/.c and test_mount_travel.c
contain species profiles, terrain movement permissions and the selected
resource to charge. They are **not an implementation of native mounts,
ownership, flight, combat, stables or durable save transactions**.


## AtlasMUD flag screenshot reference (November 21, 2026)

The user-supplied AtlasMUD monster flag screen includes a label
\`MOUNT\` at displayed position 75, alongside \`HIREABLE\` (54),
\`HIRED\` (55) and \`NOWANDER\` (76). This is useful as
**design inspiration**, not as a verified Atlas riding, stable
or Endurance implementation. Player \`dragon\`, \`bat\` and
\`gray wolf\` transformation labels are separate concepts,
and monster \`BREATH TOG 1/2\` cannot be mapped to HollowDeep's
100-point player Breath travel resource.

HollowDeep's mount system must still use independent epoch-bound
ownership, one active mount, separate Endurance and the validated
native exit/terrain/atomic save path rather than repurposing
unknown legacy flags. See
[Atlas screenshot notes](ATLAS_FLAG_SCREENSHOT_NOTES.md) for the
full observed flag categories and recommended milestones.

The Round79G status statement above is **historical**: later
[Round79 gameplay notes](ROUND79_GAMEPLAY_QOL.md) document
Round79P's privately verified native Breath and rest command,
but no native mount/Endurance/stable implementation has
yet been accepted. Round79Q real connected wall-clock +15
recovery is still unverified. Production remains unchanged.


## Round79Q acceptance and Round79R native mount foundation (November 21, 2026)

The earlier top-of-document note is historical: the user has now
verified the complete private Round79K–Q Breath/rest subsystem.
In particular, Round79Q passed 18 private regressions and
**real wall-clock +15 resting Breath recovery on a connected
socket**, with an exact single award and no immediate duplicate.
Native \`update.c:129\` calls \`update_ply(Ply[i].ply)\`. The
accepted private ELF32 source is:
\`/tmp/hd-army-game-round79rest-JQgo3wi5/src\`.
Production service PID, live executable and accepted private
ELF32 binary remained unchanged; **deployment NONE**.

Round79R begins a NEW independent, read-only mount track:
- Reuse the existing Round79G pure C species/terrain planner
  for Horse, Warhorse, Dire wolf, Nightmare, Griffin and
  Dark dragon. Mounted wilderness travel spends mount Endurance
  rather than character Breath; one active mount; no free
  travel, command spam or bypass of native exit checks.
- Extend \`native_mount_command_audit.py\` to accept the
  verified private Round79P native ELF32 rest source path;
  inspect actual \`global.c\`, \`wilderness.c\`, \`mtype.h\`
  and \`mstruct.h\` for native command collisions, potential
  mount flags and movement/terrain semantics.
- Six new source-audit safety regressions cover private ELF32
  acceptance, relevant symbol display and rejection of live
  source, ELF64, missing native headers and symlinked input.
- \`private_mount_foundation_round79r.sh\` compiles existing
  mount rules as private ELF32, runs these regressions,
  writes only root-private reports and verifies production PID,
  executable and accepted private ELF32 hash unchanged.

**Round79R is staged, not yet executed on Linode.**
This does **not** add mount ownership, stable retrieval, mounted
native movement, persistent Endurance or flying gameplay.
The AtlasMUD screenshot flag \`MOUNT\` at displayed position
75 is just a feature-design clue, not a HollowDeep-compatible
bit position. Any new persistent mount implementation must use
verified native structure/serialization rules and durable
character-epoch-bound receipts, with no unapproved live changes.


## Round79R initial private test — prefixed mount flag scanner fix

The first private Round79R Linode run stopped before the pure ELF32
mount-rule compilation and native command/flag audit. Five of the six
synthetic source-audit tests passed, but
\`test_mount_command_and_flags_reported\` failed because its synthetic
\`mtype.h\` fixture defined \`PMOUNT 75\` while the read-only scanner
looked only for the standalone \`mount\` token. A word-boundary
search does not match the \`mount\` substring in \`PMOUNT\`.

The scanner now additionally recognizes *explicitly spelled*
\`PMOUNT\`, \`CMOUNT\`, \`OMOUNT\` and \`MMOUNT\` symbols when present,
without assuming any actually exist in HollowDeep. Two new tests
check those candidate spellings and confirm that no missing mount
flag is fabricated. The audit suite now contains **eight** tests.

**The number 75 in the unit fixture is synthetic, not proof of
HollowDeep's C flag positions and not evidence Atlas's own MOUNT
position may be used as a HollowDeep offset.**

The prior attempt produced:
\`FAILED (failures=1)\` and \`PRODUCTION DEPLOYMENT: NONE\`.
It did not reach native source audit or mount/Endurance rule
compilation. Run the corrected private Round79R tool in a new
pinned checkout before claiming source-audit or ELF32 PASS.


## Round79R FINAL — mount rules + native command/flag audit PASS

The user's private Linode run \`round79r-Vbd8C3ao\` completed:
- Eight Python native-source audit/safety tests PASS.
- Existing foot-vs-mounted Endurance/terrain planner compiled and
  exercised as ELF32: \`ROUND 79G: FOOT BREATH / MOUNT ENDURANCE /
  TERRAIN RULES PASS\`.
- Read-only native command/flag audit PASS on the already accepted
  \`/tmp/hd-army-game-round79rest-JQgo3wi5/src\`.
- Actual command table \`global.c matches=0\` for mount, dismount,
  stable, ride, etc.; not evidence the words are available in every
  command/alias context, so re-check exact registration before use.
- Actual \`mstruct.h matches=0\` and \`mtype.h matches=0\` for
  selected mount/Endurance symbols. Do NOT assign Atlas's displayed
  MOUNT number 75 to any HollowDeep native bit.
- Verified wilderness \`read_tile()\` and
  \`hd79_wilderness_tile()\` in \`wilderness.c\`, along with
  \`hd_wilderness_move/go()\` wrappers around native movement.
  The map display has an independent ephemeral session structure,
  not an ownership record.
- Additional grep matches in Conjure's dragon spell and
  \`#error "Warlock requires the stable Necromancer receipt format"\`
  do NOT represent mounts or stables.
- Production PID and binary hash and accepted ELF32 binary
  checked unchanged; \`PRODUCTION DEPLOYMENT: NONE\`.

**Round79R accepted as a read-only audit and pure rule validation.**
It does NOT prove native mount ownership, stable interaction,
Endurance debit, or persistence, which remain unimplemented.
The next independent step should define a bounded **epoch-bound**
mount roster and one-active-mount transition policy and test
ownership/Endurance/rest/relog/stabling separately from the live
game before integrating with atomic save receipts.


## Round79S staged — epoch-bound mount roster and stable policy

After Round79R's real source audit PASS, a pure, versioned
policy foundation has been published:
- \`hd79_mount_roster.h/.c\` models one player's roster of up to
  **six** mounts, each with an owner-local ID, species, current
  Endurance and verified stable-room ID. The roster is
  identified by the accepted 24-character character epoch and
  has a monotonically increasing revision.
- Awarding, boarding, dismounting, stable entry/retrieval and
  movement each validate the expected character epoch.
  Malformed records, forged active IDs, invalid species,
  duplicate/stale operations, revision overflow and
  unsupported ownership transitions fail without modifying
  their output. Only **one** mount can be actively boarded.
- Stable deposit requires verified player location **and**
  physical presence of the eligible owned mount; retrieve
  requires return to the **same** verified stable.
  Remote retrieval or mounting a stabled mount is denied.
  Board/dismount/deposit/retrieve do not refill Endurance.
- \`hd79_mount_travel()\` accepts the existing Round79G terrain
  plan and an external authoritative native-movement result;
  only a successful validated wilderness move can reduce
  the currently ridden mount's Endurance. Character Breath
  remains unchanged while mounted; exit to a safe interior
  is free even when the mount is exhausted.
- \`test_hd79_mount_roster.c\` checks epoch mismatch/forgery,
  six owned mounts, one active, verified stable locality,
  exact Endurance deduction, replay of stale movement
  previews, denied terrain, exhausted mount retreat and
  overflow refusal. A new root-only runner,
  \`private_mount_roster_round79s.sh\`, compiles it alongside
  the existing mount and Breath planning rules as ELF32,
  tests the result and verifies production/service and
  accepted private ELF32 binary hashes are unchanged.

**Round79S has been staged in GitHub but not yet tested on Linode.**
This is not native ownership, a stable command, an item, an
actual ridden creature, a save or a mount reward implementation.
The policy API performs **no disk I/O**. It intentionally
defers persistent encoding and atomic CAS integration into
the native \`hd_player_store.c\` player receipt/snapshot
contract to a separate step. A candidate native mount/save
checkpoint must be tested for competing processes, failure
injection, stale epoch, disconnect/death, denied movement,
and recovery after uncertain rename before player gameplay.

The six-mount cap is a **prototype policy bound**, not a
final product cap. Mount species/endurance/costs remain
provisional from Round79G. Any eventual stable location must
be approved based on the private builder/world data rather
than guessed from the Atlas screenshot. No live deployment.


## Round79S accepted — Round79T mount two-receipt wire + native storage audit

The user's final Round79S Linode run reports the pure ELF32
six-mount roster test **PASS**:
- Epoch-bound ownership and malformed records rejected.
- Six-species cap, one active mount, verified stable locality
  and no remote retrieval/recharge PASS.
- Mounted movement subtracts Endurance exactly once, leaves
  player Breath unchanged, and allows exhausted mount retreat.
- Revision overflow/forged active-state denial PASS.
- Production service PID/binary and previously accepted private
  ELF32 executable unchanged; deployment NONE.

Round79T is an **independent, pure serialization/receipt-capacity
foundation**, not a native save integration. The existing
HDTR1-style receipt values hold 64 hexadecimal characters.
Six mounts, ownership epoch, revision and stable locations cannot
safely fit in one 64-hex record. Therefore:

1. \`hd79_mount_wire.h/.c\` serialize a canonical fixed
   **64-byte** mount record into two NUL-terminated
   **64-character lower-case hex fragments**, suitable as two
   *separate reserved receipt payloads only after IDs and
   receipt capacity are verified*. The record contains
   version, count, active mount, the 12-byte character
   epoch (24 hex chars), full uint32 revision and six
   fixed entries with species/Endurance/stabled/
   24-bit stable-room ID.
2. CRC32 protects the **combined** record against accidental
   cross-fragment mixing or corrupted/partial data;
   unused bytes and version fields must be zero/valid.
   A CRC is not a MAC or an authentication mechanism:
   ownership authorization and stale-revision denial
   remain the responsibility of the native locked
   player-save transaction.
3. \`test_hd79_mount_wire.c\` checks empty and full
   roster roundtrips, exact canonical repeat encoding,
   active/same-stable fields, max room ID, max revision,
   corruption/uppercase/bad length, output immutability
   and mixed-generation rejection.
4. \`audit_native_mount_receipt_capacity.py\` and seven
   synthetic private-source safety tests inspect the
   actual accepted \`hd_player_store.c\`,
   \`treasure_receipt.h/.c\`, and Breath/Conjure includes
   for receipt limits, reserved claim IDs, epoch
   binding, add/encode APIs and atomic snapshot contract,
   without changing any source or player data.
5. \`private_mount_wire_audit_round79t.sh\` runs the
   synthetic source tests, compiles/executes the pure
   wire tests as ELF32, produces a **root-only receipt
   capacity report**, and confirms the original private
   ELF32 and production PID/executable remain unchanged.

Round79T has **not yet been run on Linode**. Two dedicated
mount receipt IDs are **not allocated**, and no mount
persistence is wired into \`hd_player_store.c\`.
The next real persistence milestone must test that the
receipt set has space for both fragments alongside existing
Necromancer, Conjure and Breath records and must add both
fragments in one atomic snapshot under the same lock.
Check authoritative character epoch, conflicting writes,
short-write/uncertain rename, ordinary saves, relog, death,
recreated names, full receipt sets and malformed input.
No live deployment or player-world changes are authorized.

## Round 79T native integration

The [native mount implementation and runner](ROUND79T_NATIVE_MOUNTS.md) add persistent ownership, stable commands and Endurance-aware native travel in a disposable ELF32 build. The preceding notes document the earlier pure-policy and wire stages. The native candidate reserves two receipt IDs, preserves their fragments through ordinary saves, and checkpoints them with the moved character.
