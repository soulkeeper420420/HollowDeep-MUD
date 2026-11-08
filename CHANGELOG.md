# HollowDeep release notes

## 2026-11-08 — GM Stage 5A/5B bridge readiness and isolated socket test

Completed a **non-deploying** bridge-readiness inspection and six-case isolated Unix-domain socket protocol test for the proposed GM moderation integration. Stage 5A established native staff identity checks, site authentication function candidates, runtime service account and sandbox restrictions, and that no PHP-to-native identity binding or bridge currently exists. Stage 5B verified all six disposable mock tests passed: read-only capability allowance, replay rejection, mutation denial for mute and shutdown, and malformed-request rejection for identity injection and a missing request ID. The socket was removed. These results do **not** verify production admin authentication, native GM authorization, persisted replay protection or any live moderation action.

A running-executable hash check confirmed native v3 player-presence SHA-256 `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`. However, live `src_3.00/io.c` lacks the active publisher, whereas the staged v3 source contains it. **Reconcile and preserve the staged baseline before compiling**; do not rebuild from the older live source tree. The private production presence snapshot was fresh and the game service remained active. No native code, website code, service units, world or player files were changed and no MUD restart occurred. See the [VPS operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only.

## 2026-11-08 — GM Moderation Center v4 Stage 4 read-only reference installed

Added a **separate administrator-only read-only** VPS moderation reference at `/admin/gm-moderation-v4.php`. The page documents native `hstaff` and `hmoderate` operations, HollowDeep staff ranks and target protections, audit ordering, and the security prerequisites for a future native moderation RPC bridge. Source review in `hollowdeep_staff.c` shows moderator-level gates for announce/mute/unmute/kick, administrator gates for roster audit and role changes, target/rank checks, required online targets for mute/kick, and the attempt to persist an audit entry before major side effects. Audit entries are **not** definitive execution receipts; no replay protection or live web-action interface is provided.

The operator reported staged/temporary/installed `php -l` checks passed, `hollowdeep.service` active, existing GM command catalog unchanged and **no native game modifications or restart**. An authenticated mobile screenshot verified initial rendering of the `hstaff whoami`, `hstaff list`, and `hstaff audit` operation cards with expected labels. The remaining operations, full navigation, and cross-browser checks are **not yet browser-verified**. Live moderation actions remain disabled. See the [VPS investigation and operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub documentation does not deploy the VPS PHP source or disclose staff, player or audit records.

## 2026-11-08 — GM Console v4 Stage 3 native dispatcher permission labels installed

The operator installed the Stage 3 permission-label update to the separate administrator-only `/admin/live-gm-console-v4.php` page. Source inspection of `hollowdeep_help.c:20–30` verified that native `*` command IDs 101–149 normally require a native `CARETAKER` character class; IDs 106, 119, 129, 141, 144, 145, 146 and 148 require native `DM`; ID 113 (`*flushrooms`) additionally requires a configured nonempty `DMNAME2` and exact operator-name match. The dashboard now labels these **dispatcher-level** requirements while continuing to mark additional per-handler restrictions and equivalence to HollowDeep's separate staff-role model as unresolved.

The permission scanner processed 54 registrations and 49 handlers, flagging 18 high-impact handler groups for further audit. Source review resolved two definition-scanner misses (`dm_finger` and `dm_list`). The installer reported source verification passed, staged and installed PHP lint passed, an atomic PHP page replacement and a backup at `/root/hollowdeep-dev/gm-v4/backups/live-gm-console-v4-before-permissions-20261108-032231.php`. The operator confirmed `hollowdeep.service` active, 59-function catalog preserved, **GM command execution disabled**, no native game change and no MUD restart. **Stage 3 browser validation remains pending**; do not conflate source-backed labels with a complete security review. See the [VPS operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publishing does not deploy VPS PHP or source binaries.

## 2026-11-08 — Live GM Console v4 native command catalog, initial browser verification

Deployed a new administrator-only, **read-only** GM command reference at `/admin/live-gm-console-v4.php` on the separate Ubuntu VPS. Stage 1 discovered 59 `dm_*` and `hd_staff_*` native C functions in eight source files and grouped them into five preliminary categories. Stage 2 mapped the actual `global.c` command registry into 54 `*`-prefixed registrations and aliases for 49 distinct handlers, preserving the 59-function catalog. The page displays command names, native handler names, command IDs, source line references and explicit authorization uncertainty; it cannot execute GM commands.

The operator reported successful PHP lint for staged and installed pages, an active `hollowdeep.service`, no native game changes and no service restart. An authenticated mobile screenshot confirmed the registered `*teleport` card correctly displayed `dm_teleport`, command ID 101, `global.c:431`, an authorization notice and execution disabled. Search/filter behavior, all command cards and exact per-command staff permissions remain **unverified**. Native dispatcher checks and per-handler caretaker-class checks must not be mistaken for automatic parity with HollowDeep's separate player/moderator/implementor/administrator/owner staff-role hierarchy. A timestamped local v4 backup was retained. See the [VPS investigation and operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only; it does not deploy the VPS console or include private player data.

## 2026-11-08 — Live GM Console v3 authenticated player presence, production verified

Activated the native Mordor 3.00 **count-only authenticated-session publisher** in `frp.new`, backed by a strict-permission JSON snapshot at `/var/lib/hollowdeep/gm-presence/status.json`, a schema/freshness/ownership-validating extension to the existing root-run GM monitor, and an admin-only `/admin/live-gm-console-v3.php` dashboard. The dashboard distinguishes authenticated characters from established TCP connections; missing or stale native data appears as **Unavailable**, not zero. No character names, IP addresses, messages or credentials are published and GM commands remain disabled.

The isolated 32-bit GNU89 build passed six simulated authenticated-session cases and 100 private JSON sample writes. A first production activation could not create the native snapshot because `ProtectSystem=strict` blocked writes to the new directory; automatic rollback restored the original executable. A narrow systemd `ReadWritePaths` allowance for `/var/lib/hollowdeep/gm-presence` corrected the problem while retaining the strict sandbox. Subsequent supervised production activation reported the game and monitor active, and operator browser screenshots confirmed the full transition **0 players → 1 authenticated player on login → 0 after logout**, with TCP connections also returning to zero and the game service remaining active. The publisher writes periodically from the main game loop; offline benchmarks do not guarantee production I/O latency.

Original binary SHA-256 `0aaca56032fe1454b4cab4e2cd7a3ac2bbb2e5c03632b825bf0ae395c50f40ad`; deployed v3 candidate SHA-256 `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`. Root-only release backup and manual rollback procedure remain on the VPS. See the [VPS investigation and operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub documentation change does **not** deploy the VPS application or publish private native/player data.

## 2026-11-08 — Live GM Console v2 browser-verified

Installed the separate admin-only `/admin/live-gm-console-v2.php` page, the read-only collector `/usr/local/libexec/hollowdeep-gm-monitor.py`, and a dedicated systemd service/timer refreshing `/var/lib/hollowdeep/gm-monitor/status.json` approximately every minute. The monitoring snapshot identifies `hollowdeep.service` as active with native executable `frp.new`, its own TCP 4040 listener and a point-in-time count of 1 established TCP connection (not an authenticated player count). The PHP dashboard checks snapshot freshness and shows process/service/socket status while keeping GM commands disabled and player presence labeled unavailable. Staged and installed PHP lint passed, the monitor timer was active, and the operator confirmed all authenticated browser tests passed including freshness. The installer did not change or restart the native game; only its separate monitoring service/timer was enabled. See the [VPS investigation and operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub documentation does not deploy VPS code or expose player data.

## 2026-11-08 — Live GM Console v1 browser-verified

Installed the separate administrator-only **Live GM Console v1** at `/admin/live-gm-console.php` on the VPS. It shows read-only host uptime, one-minute load, memory/disk capacity, possible MUD process names, numeric room-snapshot counts, world-report readability/age, private builder draft/proposal counts, recent investigation-audit status activity (without note text), and links to existing World Builder v1–v5 and investigation tools. The operator confirmed dashboard metrics, safe process visibility, world monitoring, audit presentation, navigation, and lack of command execution controls in the authenticated browser. Installer: `/root/install_hollowdeep_gm_console_v1.sh`; staged and installed PHP lint passed, and the page was new. Process-name detection is heuristic; the release **does not** establish online player count or offer GM commands, and it did not alter or restart the native Mordor game. See the [VPS operations guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only and contains no private audit or player data.

## 2026-11-08 — World Builder Studio v5 browser-verified

Installed the standalone administrator **World Change Impact Analyzer v5** at `/admin/world-builder-impact.php`. It reads existing room JSON snapshots and private v3 proposal records to show a clickable two-hop/25-node schematic impact map, incoming and outgoing room connections, comparisons of detected current exits and explicitly proposed exits, related proposal dependencies, advisory impact warnings and a pre-deployment review checklist. The operator reported staged and installed PHP lint passed and confirmed room 1508 selection, map navigation, connections, proposal comparisons, warnings when applicable and v1–v4/investigation links in the authenticated browser. Installer: `/root/install_hollowdeep_world_builder_v5.sh` (new PHP page, no prior v5 backup). Omitted proposed exits do **not** mean deletion; warnings are heuristics rather than native Mordor compatibility checks. Source room snapshots, private v3 proposals, live game binaries and MUD services were not changed. See the [VPS investigation and World Builder guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only; it does not deploy PHP or private data.

## 2026-11-08 — World Builder Studio v4 browser-verified

Installed standalone administrator **World Package Review v4** at `/admin/world-builder-packages.php`. It reads existing private v3 proposals without modifying them and provides package-level status counts, validation warnings for source-room/zone/name drift, malformed or inconsistent structured exits and missing destinations, detection of links to other proposed rooms, zone/status-filtered change-review tables, and links back to v3. It also offers an on-demand JSON review manifest with proposal identifiers, statuses, proposed zones/exits, dependencies and warnings, but excludes full builder notes and descriptions. The operator confirmed the summary, filters, warnings/dependencies when applicable, proposal navigation and JSON download in an authenticated browser. Installer: `/root/install_hollowdeep_world_builder_v4.sh`; staged and installed PHP lint passed; the page was new. The review manifest is not a deployable world package and needs private handling. No world files, private proposals or MUD services were changed. See the [VPS investigation and World Builder guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only and does not deploy PHP or private records.

## 2026-11-08 — World Builder Studio v3 browser-verified

Installed a standalone administrator **World Builder v3 Proposal & Review Studio** at `/admin/world-builder-review.php` with private per-room proposed names, descriptions, zones, structured `direction:destination` exit plans, validation against existing snapshot destination IDs, duplicate-direction detection, a zone planning summary, and a change-review queue offering Draft and Ready for Review states. Saved proposals reside only in the separate private `/var/lib/hollowdeep/world-studio/proposals/` directory. The operator confirmed the editor, save/reload persistence, valid and invalid exit handling, workflow state, queue, zone planning and v1/v2/investigation links in the authenticated browser. Installer `/root/install_hollowdeep_world_builder_v3.sh` reported both staged and installed PHP lint passed; the page was new, with no existing version to back up. Neither review status nor saving deploys changes to the MUD; native world files and processes were not altered. See the [VPS investigation and World Builder guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only and excludes private proposal files.

## 2026-11-08 — World Builder Intelligence v2 browser-verified

Installed separate admin-only VPS PHP **World Builder Intelligence v2** at `/admin/world-builder-intelligence.php`. It provides snapshot-derived room and exit statistics, missing-destination and missing-reciprocal-exit checks, a clickable two-link/25-node schematic room network centered on the selected room, incoming and outgoing connections, a private v1 draft inventory, side-by-side comparisons of snapshots and proposed descriptions/names, and direct links to v1 editing and existing investigation tools. The operator reported that PHP lint passed both before and after installation, and that room 1508 navigation, graph and counts, exit listings, draft comparisons when present, and investigation links passed authenticated browser verification. The new page reads snapshots and draft records without modifying them; exit anomaly counts depend on supported JSON fields and do not necessarily match the full connection report. See the [VPS investigation and World Builder guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub documentation is not a VPS PHP deployment and does not include private drafts, native game modifications, or server restarts.

## 2026-11-08 — World Builder Studio v1 browser-verified

Installed a new admin-only VPS PHP **World Builder Studio** at `/admin/world-builder-studio.php`, providing a schematic SVG room-connection map, room search, zone browsing where snapshot metadata supports it, room inspector and exit listing, private per-room proposed name/description/exits/notes drafts, and navigation into existing investigation tools. A staged and installed PHP syntax check passed; the operator confirmed the map, room 1508 search, zone UI, draft persistence, and investigation links in the authenticated browser. Installer: `/root/hollowdeep-dev/world-studio/install_v1.py`. The new page had no previous version to back up. Draft JSON is stored privately under `/var/lib/hollowdeep/world-studio/drafts/` and is **never applied to live game data** by this release. See the [VPS investigation and World Builder guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication documents the VPS install; it does not deploy PHP, private drafts, or room files, and does not restart the MUD.

## 2026-11-08 — Step 144 Clear Sort browser-verified

The VPS administrator Operations Overview now has a contextual **Clear Sort** link that resets Oldest first to Newest first while preserving the activity, search, change type, UTC date range and page-size settings, and returning pagination to Page 1. The operator confirmed the shortcut with filters selected and verified that Clear Dates, Clear Search, Clear Change Type, Clear Activity Filter, Reset Filters, and View History still work in the authenticated browser. Installer backup: `operations-overview.php.before-step144-20261108-001632`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub documentation commit does not deploy PHP, expose private records, or modify/restart the native MUD.

## 2026-11-08 — Step 143 Clear Activity Filter browser-verified

The VPS administrator Operations Overview now includes a contextual **Clear Activity Filter** shortcut that restores All Activity while preserving search text, change type, UTC date range, sort order and page size, and resets pagination to Page 1. The operator verified the shortcut from Status Changes and Notes Changes and confirmed Clear Search, Clear Dates, Clear Change Type, Reset Filters and View History still work in the browser. Installer backup: `operations-overview.php.before-step143-20261108-001441`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub update documents a separately installed VPS PHP change without deploying PHP, disclosing private audit records, or altering/restarting the native MUD.

## 2026-11-08 — Step 142 Clear Change Type browser-verified

The VPS administrator Operations Overview now provides a contextual **Clear Change Type** link, returning the change-type selector to All Changes while retaining activity, search, UTC dates, sort and page size and resetting to Page 1. The operator browser-verified the shortcut from Status Only and Notes Only and confirmed preserved selections, Clear Dates, Clear Search, Reset Filters, and View History. Step 142 backup: `operations-overview.php.before-step142-20261108-001329`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub publication is documentation only and does not deploy PHP, publish private records or modify/restart the live MUD.

## 2026-11-08 — Step 141 Clear Search browser-verified

The VPS administrator Operations Overview now has a contextual **Clear Search** link, which empties only the audit text search, retains activity, change type, UTC date range, sort and page size, and resets to Page 1. The operator browser-verified it with other filters selected, including confirmation that Clear Dates, Reset Filters, clickable audit cards and View History still function. Installer backup: `operations-overview.php.before-step141-20261108-001220`; staged and deployed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub publication documents separately installed PHP only; it does not deploy PHP, publish private audit records or modify/restart the native MUD.

## 2026-11-08 — Step 140 Clear Dates browser-verified

The VPS PHP Operations Overview now provides a contextual **Clear Dates** shortcut that removes only audit From/To date restrictions, preserves the activity, text-search, change-type, sorting and page-size settings, and returns to Page 1. The operator verified preset and open-ended dates, preserved controls, Reset Filters, all four audit cards and View History in the authenticated browser. Installer backup: `operations-overview.php.before-step140-20261108-001115`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub documentation commit neither deploys PHP nor publishes private records or restarts/modifies the MUD.

## 2026-11-08 — Step 139 All Audit Events card browser-verified

The VPS Operations Overview now offers a fourth clickable audit breakdown card, **All Audit Events**, which clears only the change-type filter while retaining activity, search, date range, sort and page-size selections and resetting to Page 1. The full-history event total remains stable across filtered views. The operator confirmed all card links, preserved controls, Reset Filters and View History in the authenticated browser. Backup: `operations-overview.php.before-step139-20261108-000940`; staged and deployed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub publication does not deploy PHP, publish private data or modify/restart the MUD.

## 2026-11-08 — Step 138 clickable audit breakdown browser-verified

The VPS administrator Operations Overview now makes its three full-history audit breakdown counters clickable, setting the corresponding Change Type filter while retaining search, date, sorting, activity and page-size settings and resetting to Page 1. The selected card is marked for the operator. The operator browser-verified all three cards, stable totals, Reset Filters and View History. The Step 138 installer saved `operations-overview.php.before-step138-20261108-000813`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication is documentation only; it does not deploy PHP, expose private audit records, or touch native MUD processes.

## 2026-11-08 — Step 137 audit change-type filter browser-verified

The VPS Operations Overview now filters audit activity by All Changes, Status Only, Notes Only, and Status & Notes while keeping the full-history breakdown counters independent of filtering. The filter combines with existing search, date presets, sort and pagination, and Reset Filters restores All Changes. The operator confirmed the four choices and existing navigation in the authenticated browser. Installer backup: `operations-overview.php.before-step137-20261108-000651`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub documentation update does not deploy PHP, publish private records, or touch the running MUD.

## 2026-11-08 — Step 136 audit change breakdown browser-verified

The VPS Operations Overview now displays full-history audit counts for Status Changes Only, Notes Changes Only, and Status & Notes Changed; events with neither recorded change are accounted for separately. Counts are calculated before filtering so they do not fluctuate with search, date ranges, sorting or pagination. The operator confirmed the counters, totals and View History drilldown in an authenticated browser. The Step 136 installer saved `operations-overview.php.before-step136-20261108-000507` and passed PHP lint before and after installation. See the [VPS investigation console guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub documentation publication does not deploy PHP, publish private audit data, or modify or restart the native MUD.

## 2026-11-07 — Step 135 quick UTC date presets browser-verified

The VPS Operations Overview now offers Today (UTC), Last 7 Days and Last 30 Days audit date shortcuts, retaining search, activity filter, sort and page size while returning to Page 1. The operator verified the three presets, preservation of selections, and Reset Filters in the authenticated browser. The Step 135 installer saved `operations-overview.php.before-step135-20261107-235454`; staged and deployed PHP lint passed. The [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md) describes the controls. This GitHub documentation commit does not deploy PHP, include private audit data, or alter/restart the native MUD.

## 2026-11-07 — Step 134 Reset Audit Filters browser-verified

The VPS Operations Overview now offers a contextual Reset Filters link that restores All Activity, an empty search/date range, Newest first, five events per page and Page 1. The operator confirmed the reset and existing View History drilldown in the authenticated browser. The installer retained `operations-overview.php.before-step134-20261107-235258`; both staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This commit publishes documentation only: no VPS PHP deployment, private audit data publication, native MUD changes, or restarts.

## 2026-11-07 — Step 133 UTC audit date range browser-verified

The VPS Operations Overview now filters matching audit activity by optional UTC From Date and To Date, validating calendar dates and reporting an invalid reversed range. The operator confirmed same-day and open-ended date filtering, reversed-date validation, preserved selections through search/sorting/pagination, and View History drilldowns in the browser. The installer backed up `operations-overview.php.before-step133-20261107-235104`; staged and installed PHP lint passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub commit records separately installed VPS PHP work; it does not publish private audit records, deploy PHP, or alter/restart the native game.

## 2026-11-07 — Step 132 audit chronological sorting browser-verified

The VPS PHP Operations Overview now supports Newest first and Oldest first sorting of matching audit events, preserving activity filters, audit search, page size, Previous/Next, Go to page, and View History. The operator confirmed the sorting and navigation scenarios in the authenticated browser with six existing events. The installer saved `operations-overview.php.before-step132-20261107-234939`; staged and deployed PHP lint checks passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub publication documents a separately installed VPS PHP change; it does not publish private records or change/restart the native MUD.

## 2026-11-07 — Step 131 adjustable audit page size browser-verified

The VPS Operations Overview now offers a Results per page selector with choices **5, 10, 25 and 50**. Page size is retained across previous/next pagination and direct page jump along with existing activity filters, audit search, and View History links. The operator confirmed the four page-size options and existing navigation/search functionality with six saved audit events. The installer preserved `operations-overview.php.before-step131-20261107-234823` and passed PHP syntax checks before and after installation. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). GitHub publication documents the separately installed VPS PHP change; no private records, game files or service restarts are involved.

## 2026-11-07 — Step 130 direct audit page jump browser-verified

Added a Go to page numeric control to the VPS Operations Overview's paginated audit activity list. The control retains activity filters and search queries, uses the existing bounded page range, and preserves per-event View History links. The operator verified browser navigation between pages 1 and 2, filter/search retention, and history drilldown. The installer retained `operations-overview.php.before-step130-20261107-234638`; staged and deployed PHP lint passed. See the [VPS investigation console guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub publication is documentation only and does not deploy PHP, expose private audit data, or modify/restart the native MUD.

## 2026-11-07 — Step 129 audit search pagination browser-verified

The VPS Operations Overview now paginates matching Recent Audit Activity at five events per page with Previous/Next links, preserving the activity filter and search query. The operator confirmed browser navigation across the existing six events (five on page one and one on page two), search/filter retention, and View History links. The installer saved `operations-overview.php.before-step129-20261107-234426`, and staged and installed PHP lint passed. The total Audit Events card remains unchanged by filters. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This publication documents a PHP website change already installed on the VPS; it does not deploy source, publish private records, or touch/restart native MUD services.

## 2026-11-07 — Step 128 Operations Overview audit search browser-verified

The VPS PHP Operations Overview now supports a GET `audit_q` search (100-character limit) over administrator names, finding identifiers and old/new review statuses, combined with the existing All/Status/Notes activity filter. The operator confirmed browser searches, retained query text, combined filters, and per-event View History links. The installer retained `operations-overview.php.before-step128-20261107-234036` and passed staged and installed PHP lint. The page continues showing the latest five matching entries while the summary reports all audit events. The [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md) now documents this verified behavior. This repository commit records the separately deployed VPS feature; it does not deploy PHP, include private audit records, or modify/restart the game.

## 2026-11-07 — Step 127 audit activity filters browser-verified

On the VPS PHP Operations Overview, added an activity selector for All Activity, Status Changes and Notes Changes. The view shows up to five latest matching events without changing the total Audit Events count; the existing per-event View History links remain available. The operator reported that **all three filter choices and the history link passed browser verification**. The installer saved `operations-overview.php.before-step127-20261107-233821`; both staged and installed PHP lint checks passed. See the [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md). This GitHub commit documents the VPS installation; it does not deploy PHP, publish private audit data, or modify or restart the native MUD.

## 2026-11-07 — Step 126 audit history drilldown browser-verified

Added a Finding History column to the deployed PHP Operations Overview Recent Audit Activity table on the VPS. Its per-event View History link targets the matching finding's authenticated audit history; nonconforming IDs do not become links. A timestamped backup (`operations-overview.php.before-step126-20261107-233545`) was retained, staged and installed PHP lint passed, and the operator confirmed the link works in the browser. The [VPS investigation guide](docs/VPS_INVESTIGATION_CONSOLE.md#step-126--recent-audit-history-drilldown-host-verified-november-7-2026) documents the change. This GitHub commit publishes documentation only; no PHP deployment, game modifications, or MUD restart was performed by GitHub.

## 2026-11-07 — Step 125 Operations Overview installed and browser-verified on VPS

Installed `/admin/operations-overview.php` on the Ubuntu PHP website via the VPS-local Step 125 installer. The installer created a timestamped Admin Dashboard backup (`dashboard.php.before-step125-20261107-232947`), added navigation to the Operations Overview, and passed PHP syntax checks for both files. The operator confirmed the page loaded and displayed correctly in the browser. The read-only, admin-only page shows investigation totals, review progress, latest audit events, monitoring guidance, and links to administrator tools. See the [VPS investigation-console guide](docs/VPS_INVESTIGATION_CONSOLE.md#step-125--operations-overview-host-verified-november-7-2026). This GitHub update documents the VPS work only; it does not deploy PHP, publish private audit data, or alter/restart the game. Scheduled cron success after the logging change remains separately unverified.

## 2026-11-07 — Step 123 audit monitor success logging installed and manually verified

On the VPS, the operator backed up `/usr/local/bin/hd-audit-alert` to a timestamped `.before-step123-` copy, installed a shell-syntax-checked wrapper, and ran one manual check. The wrapper now logs UTC `AUDIT OK` on healthy checks and `AUDIT RECOVERED` when the failure marker clears. It keeps failure-only Discord alerts and duplicate-alert suppression; routine success does not post to Discord. The manual invocation logged `2026-11-07T23:25:01Z AUDIT OK` in `/var/log/hd-audit-health.log`. Immediately afterward, `hd-admin` reported valid audit JSON (2 saved findings, 6 events), acceptable permissions, active cron, configured hourly alerts, and a previously observed 23:00 UTC cron launch.

**Verification boundary:** The 23:25 entry came from a **manual invocation**, not cron. A scheduled `AUDIT OK` line has **not yet been observed** after this change. The revised script was installed directly on the VPS; this GitHub commit documents that host change only and does not deploy the script or touch live MUD processes. The private Discord webhook and audit records remain excluded.

## 2026-11-07 — Step 122 cron launch and audit health verified on VPS

The operator ran `hd-admin` on the HollowDeep VPS. Output: `Audit JSON OK | saved findings: 2 | events: 6`; `Permissions: OK`; `Cron service: active`; `Hourly alert: configured`; and `Scheduled cron launch: observed: 2026-11-07T23:00:01.622974+00:00`. This verifies the deployed helper's read-only health checks and observed scheduled **launch**, but does **not** prove that the scheduled audit check itself completed successfully. No native MUD files or processes were modified by this documentation update.

## 2026-11-07 — Additional PC verification of investigation Save and audit persistence

The VPS operator observed a real HTTP `POST /admin/room-investigation-status.php` returning **303**, followed by a **200** response from the Investigation Queue. An immediate read-only check showed **2 saved findings** and **6 audit events** in private VPS storage. This confirms another successful Save request and persistent records beyond the earlier four-event check. It does not establish that all six events correspond to this single POST or prove crash-safe two-file transactions. The published guide remains applicable; no live MUD code, room binaries, or services were changed by this documentation update.

## 2026-11-07 — Step 122 cron execution evidence added to hd-admin

Published an update to `tools/hd-admin.py` that looks for a cron `CMD` entry launching `/usr/local/bin/hd-audit-alert` in syslog or the cron journal, and reports an observed launch or `not yet observed (or logs unavailable)`. This avoids mistaking cron configuration reloads for job execution and eliminates repeated manual greps. It cannot prove the health check succeeded, and the upgraded version's actual Linode run is still pending. The source update and guide are committed on GitHub; existing VPS cron, webhook, audit records, game files, and services were not changed by this GitHub publication.

## 2026-11-07 — Step 119 one-command private backup verified on Linode

The operator ran `hd-admin backup` after verifying the one-command health check. The command reported `PRIVATE BACKUP OK` with a private archive in `/root/hd-audit-backups/` and `No live files were restored or changed.` Its implementation locks the same audit review lock while copying and verifies expected archive entries and archived status JSON. This is a successful private archive creation/validation test, **not** a full restoration test or proof of two-file transactional audit writes. Private backups and webhook credentials were not published. No live MUD data or services were changed.

## 2026-11-07 — Step 118 VPS one-command tool installed and verified

The operator installed the published `tools/hd-admin.py` on the Linode at `/usr/local/bin/hd-admin` and ran its default health check. The output confirmed valid audit JSON, one saved investigation, four audit events, correct private storage permissions, an active cron service and a configured hourly alert entry. This establishes that the read-only `status` command works on the host; the separate `hd-admin backup` command has not yet been tested there, and actual scheduled cron execution remains unconfirmed. No MUD service was restarted.

## 2026-11-07 — Step 118 one-command VPS audit administrator published

Added [`tools/hd-admin.py`](tools/hd-admin.py), a standard-library Python helper for the separate VPS PHP investigation console. The default `hd-admin` command reads and validates status/audit JSON, checks private permissions and existing hourly cron configuration. Explicit `hd-admin backup` acquires the PHP-compatible exclusive lock and creates a private validated backup archive under `/root/hd-audit-backups`. The script contains no credentials, webhook URLs or private audit data. No game binary changes, MUD restarts, automated live deployments or GitHub/Discord posting actions were added. This source was published to GitHub; **Linode installation and live execution remain unverified**.

## 2026-11-07 — Steps 100–108 private audit permissions and hourly Discord failure monitoring

VPS operator confirmed the investigation review directory is mode `700`, owned by `www-data`, with three private files at mode `600`. An hourly root cron entry was installed for `hd-audit-alert`, cron was active, and a manual healthy test reported `MONITOR OK`. Private health logging and a four-week `logrotate` policy were configured; adding `su root root` cleared the logrotate dry-run permissions warning.

A replacement Discord webhook was stored as a root-owned mode-`600` private file and returned HTTP 200 to a status-only check. The failure-alert wrapper uses a marker to suppress duplicate messages until the health check recovers. A simulated checker failure produced an alert that the operator **confirmed receiving in Discord #change-log**, followed by a successful normal check. This does not verify actual cron execution or full audit transactionality. Actual PHP and shell changes were made on the VPS; this GitHub update documents the observed setup and never includes the private webhook or investigation data.

## 2026-11-07 — Step 99Z reusable audit health command verified

The VPS operator created root-only `/usr/local/bin/hd-audit-check` to parse private `statuses.json` and all nonempty `history.jsonl` entries, then report the audit event count. The mobile terminal returned `AUDIT HEALTH OK` and `4`. The check does not detect tampered-but-valid JSON, missing events, or transactional inconsistencies. Only documentation was published to GitHub; the private data remains on the VPS, with no native MUD changes.

## 2026-11-07 — Steps 99X–99Y backup compression and recovery-read verified

Host operator confirmed `gzip -t` returned `BACKUP OK`, then streamed the archived `investigation-reviews/statuses.json` through the JSON parser with `RECOVERY READ OK`. This provides evidence the archive's compressed stream and status JSON can be read without modifying live files. It does **not** verify a complete restoration, consistency of a backup taken during a simultaneous write, or crash-safe audit transactionality. Private backup data stays on the VPS and was not uploaded.

## 2026-11-07 — Steps 99U–99W private audit backup checks

On the VPS, a root-only backup directory was created and an approximately 550-byte compressed `investigation-reviews` archive retained privately. The statuses JSON parsed successfully and four recorded audit events were valid JSON. `tar -tzf` confirmed the archive's visible directory listing includes `history.jsonl`, `statuses.json` and `statuses.lock`. This does not establish a full restore test or transactional durability. Private backup contents were **not** uploaded to GitHub or Discord. No game files or services were touched.

## 2026-11-07 — Step 99S audit write-order improvement (VPS)

The operator installed a PHP endpoint patch moving the audit-history append to after the atomic status-file rename, with a timestamped backup and passing PHP lint. A later mobile terminal check showed four entries in `history.jsonl` (earlier verification showed two), consistent with further audit recording. The exact source of each additional entry was not independently inspected. This reduces the risk of recording a successful audit event when the status rename fails, **but is not a fully transactional update**: an audit append failure may now leave a saved status without history. The PHP change occurred on the VPS; this commit documents it only and does not deploy code or restart the MUD.

## 2026-11-07 — Step 99R mobile audit history cards verified

The VPS operator added `history-mobile.css` to the admin Audit History page after creating a backup, and `php -l` passed. The authenticated mobile screenshot confirms stacked audit cards instead of a sideways-scrolling table. Fields include timestamp, administrator, finding, previous/new status and whether notes changed. Two events are visible: `awaiting` → `follow_up`, and a later `follow_up` → `follow_up` update with notes changed. This is a VPS website change documented in GitHub, not a GitHub-driven deployment. Audit write ordering remains a separate reliability improvement; the MUD server was not modified.

## 2026-11-07 — Step 99Q mobile investigation cards verified

On the live VPS, the operator added `queue-mobile.css` and included it in `room-investigation-queue.php`, after backing up the queue. PHP lint passed. An authenticated phone screenshot verified vertical investigation cards showing priority, category, room source/destination, detail, Inspect and History links, persisted Room 1508 notes, Review status and Save without horizontal table scrolling. This was a VPS website change; GitHub documentation publication does not itself deploy PHP/CSS, and no live Mordor MUD files or services were changed. Desktop regression testing and stronger audit transactionality remain future work.

## 2026-11-07 — VPS admin investigation notes and audit history verified on mobile

Host operator verified the separate PHP investigation console on `hollowdeepmud.com`: a status Save returned HTTP 303; `statuses.json` grew from 3 to 186 bytes and `history.jsonl` from 0 to 231 bytes. The authenticated Audit History viewer displayed the event; the Admin Dashboard navigation link was added and verified in the mobile browser. The Investigation Notes field was visible, and the Room 1508 note remained after Save and refresh. Shared progress showed 609 awaiting and one Follow-up Required finding.

These results verify **basic live save, audit and mobile-navigation behavior**, not transactional audit reliability. The audit append still precedes the atomic status replacement, creating a possible phantom event if the subsequent write fails. The mobile investigation queue was subsequently improved; see the Step 99Q entry above. This changelog records the existing VPS work, not a deployment of PHP from this GitHub repository; no game source, world binaries or MUD services were changed.

## 2026-11-07 — Initial VPS investigation-console documentation (historical status)

Published [VPS investigation-console guide](docs/VPS_INVESTIGATION_CONSOLE.md) describing the separate Ubuntu/PHP administrator room diagnostics, report snapshot inputs, review workflow, safe checks and publication boundaries. The reported room analysis includes 4,030 snapshot rooms and 9,551 exits. This documentation release does not change or restart the native game or VPS website.

**Historical note:** At this stage, the first Save checks had not produced persistent data. Later live testing on the same date confirmed saves and audit records; see the verified entry above. Discord webhook posting was subsequently confirmed by the operator; automatic GitHub release announcements still require the repository secret and separate workflow verification.

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
