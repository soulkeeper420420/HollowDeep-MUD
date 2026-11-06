# HollowDeep release notes

## 2026-11-06 — One-file updater

Added `hollowdeep-update.py`: upload one file and run `python3 /root/hollowdeep-update.py`. It embeds the existing reviewed installers, verifies their hashes and chooses the matching completed installation or its own known rollback. Unknown/unfinished records are refused. Existing updater safeguards and source payloads are unchanged. Twelve launcher tests cover version selection, bundle integrity, malformed records, no-install verification and child error handling. This does not establish live installation.

## 2026-11-06 — Command discovery, staff tools and release planning

Status: tested source and installation packages. **Installation of this release on the live Linode is not verified.** The last host-confirmed completed installation is the earlier spells update. The failed builder attempt stopped in a disposable test before activation.

### Player commands and help

- `spells` / `spell` list learned spells alphabetically with current/maximum mana.
- `skills` lists existing native skills allowed by class and level; `skills all` describes the full 18-skill catalog. Cooldowns, equipment and target rules still apply.
- `help` now builds a paginated alphabetical index from all 315 registered command names/aliases. Use `help commands [page]`, `help all [page]`, `help social [page]` and `help search <text> [page]`.
- Every registered command has a help page. Exact aliases and high-position social commands work; duplicate registrations appear once. `help search` explains the native search action; `help spells` keeps the original spell catalog.
- `dmcommands` / `dmhelp` lists role and builder tools. `dmcommands native [page]` lists permitted original caretaker/DM commands. A common native-class check also protects previously unguarded `*memory` dispatch; existing target/named-operator restrictions remain.

### Staff roles, world building and events

- Implementor is a separate stored role with Moderator-level authority. Existing role IDs are preserved; permission comparisons use ranks.
- `[OWNER]`, `[ADMIN]`, `[MOD]` and `[IMPLEMENTOR]` identify staff in `who`, `whois`, rosters and announcements. Original visibility rules are retained.
- The **HollowDeep Staff** clan provides role-derived membership, a roster and private online chat through `staffclan` / `hstaffclan`. Mutes apply; revocation removes access immediately. Builder-only characters and ordinary players are excluded.
- Owners assign nonoverlapping builder room ranges, 50 rooms by default. `hbuild` edits permitted rooms; `hdm` applies scoped movement/restoration with hierarchy and combat checks. Range assignment does not imply the selected rooms are empty.
- Timed monster XP/gold events allow Moderator/Implementor **1–5× for 1–60 minutes**, Admin **1–10× for 1–1,440 minutes**, Owner **1–20× for 1–1,440 minutes**. Events persist through restart, expire by time, do not stack, and preserve creator-rank stop restrictions. Trades, quests and existing coins are excluded.
- Reward calculations and coin pickup clamp signed 32-bit overflow at their new event integration points. This is not a claim that every legacy progression path has been redesigned.

### Reliability and packaging

- Fixed the original five-word command parser overflow exposed by `hbuild name Hall of the Seven Lanterns`. Bounds and termination checks preserve full command text for extension handlers while retaining compiler fortification.
- Guarded updater variants target the completed spells, parser-repair and original legacy installations separately. They verify predecessor metadata/source/binary, test a disposable candidate before activation, preserve world/saves/settings, and retain recovery records.
- Refreshed the downloadable workshop kit and allowed its original negative-numbered push/press help page through the path validator.
- Published matching player/staff/building/server guides, a full command reference, source-derived XP research, three proposed level 1–50 curves, Atlas research and future quest-area/release designs.

### Validation

Passed: full fortified ELF32 multiplayer runtime and save/reload tests; 1,869 help/skills/staff-clan permission assertions; all 315 registered names covered by help files; 263 building/DM/event checks; 80 staff checks; 70 stance checks; 144 extension checks; 1,052 normalization assertions; 23 original input integration assertions; 14 parser regression cases; native monster reward/20×/overflow/expiry checks; 7 preparation tests; 17 runtime-client tests.

Deployment checks passed: 23 native updater, 11 console packaging, 7 public activation, 15 bridge installer and 12 historical recovery tests. Client/bridge tests passed (73), TypeScript passed, and the production website build passed. Each packaged updater's embedded engine source was checked against the reviewed release tree. GitHub CI status is separate and should be checked on the published commit.

### Planned, not activated

No XP curve, training price, level cap, new class/spell, remort or gear-gated quest area changes are activated. [Future releases](docs/FUTURE_RELEASES.md) explains dependencies; [level research](docs/LEVELS_AND_EXPERIENCE.md) documents the level-25 XP cliff, monk progression issue and stat-array bounds that need work first. Website publishing and live native installation remain separate operations.

Use the [server guide](docs/SERVER_GUIDE.md) to select the matching updater. The superseded failing builder package must not be used for this release.
