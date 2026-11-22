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
