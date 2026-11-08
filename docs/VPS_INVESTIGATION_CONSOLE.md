# VPS Investigation Console: status and publication guide

> Scope: PHP administrator investigation console on `hollowdeepmud.com`, operated on the Ubuntu 24.04 VPS. This is **separate** from the repository's browser/Sites frontend and native Mordor updater. GitHub publication does not deploy this console.

## Available read-only diagnostics (host-reported, November 7, 2026)

- Room JSON snapshots: `/var/lib/hollowdeep/room-browser/[room_id].json`; reports are generated from snapshots, not live room binaries.
- World connection report: `/var/lib/hollowdeep/room-browser/world-connection-report.json`.
- Incoming exit index: `/var/lib/hollowdeep/room-browser/incoming-exits-index.json`.
- Admin pages: `/admin/world-connections.php`, `/admin/world-connection-inspector.php`, `/admin/room-investigations.php`, `/admin/room-investigation-queue.php`, and `/admin/room-investigation-history.php`.
- Current report: 4,030 rooms, 9,551 valid exits, 12 missing destination exits, 552 one-way exits, 38 isolated rooms and 8 duplicate groups. These are snapshot-analysis findings; they are not instructions to change live room data.
- Room 3470's binary exists but appears unusually short; its missing snapshot merits manual inspection. Do not call the game room corrupted without further proof.

## Review workflow and verified November 7 browser test

The queue and endpoint contain forms for statuses `awaiting`, `reviewed`, `follow_up` and notes up to 8,000 bytes. The intended storage is private, outside the webroot:

- `/var/lib/hollowdeep/investigation-reviews/statuses.json`
- `/var/lib/hollowdeep/investigation-reviews/statuses.lock`
- `/var/lib/hollowdeep/investigation-reviews/history.jsonl`

The form POSTs to `/admin/room-investigation-status.php`. Its source uses admin authentication, CSRF validation, finding ID validation against the current report, exclusive file locking, and an atomic status-file rename. The audit append runs only when status or notes actually change.

**Verified on the live VPS and mobile browser, November 7, 2026:** A POST to `room-investigation-status.php` returned HTTP 303; after the change, `statuses.json` contained 186 bytes and `history.jsonl` 231 bytes (previously 3 and 0 bytes). The authenticated Audit History page displayed the administrator's event. The Investigation Queue displayed 609 awaiting findings and one Follow-up Required finding. The Room 1508 investigation note appeared in the Notes editor and, per operator confirmation, survived Save and browser refresh. The Audit History link is also visible and works in the Admin Dashboard navigation. These are **manual functional checks**, not a full reliability or security audit; no native game deployment or restart occurred.

**Step 99S write-order improvement (host-reported, November 7, 2026):** The VPS operator moved the existing audit append block to after the successful atomic status-file replacement in `room-investigation-status.php`. A timestamped backup was retained, `php -l` passed, and the audit log subsequently contained four events (earlier evidence showed two). This supports basic continued audit logging following the update; it does **not** independently prove the exact number of events attributable to the test. Two-file durability remains nontransactional: an audit append failure after the status rename may leave a saved status without a history event. Do not describe the audit as fully atomic or crash-safe.


## Mobile investigation queue (Step 99Q)

On November 7, 2026, the operator backed up the deployed `/admin/room-investigation-queue.php`, added a separate `queue-mobile.css` stylesheet, and included it from the queue page. The stylesheet uses a mobile media query (up to 700px) to display each investigation table row as a vertical card, with labeled priority, category, source, destination and detail, followed by existing Inspect, View History, Investigation Notes, Review status and Save controls. Desktop table layout is intended to remain unchanged. `php -l` passed, and an authenticated mobile screenshot confirmed the rendered card layout with the saved Room 1508 note and controls visible without sideways scrolling. This is visual verification, not full cross-browser or desktop regression testing. The website PHP/CSS change was performed on the VPS, **not** deployed from this repository. Before publishing actual website source here, review and sanitize the deployed files.

## Mobile audit history (Step 99R)

On November 7, 2026 the VPS operator backed up `room-investigation-history.php` and added `history-mobile.css`, included from the page. At screen widths up to 700px, the six-column audit table renders each event as a vertical card with Date, Admin, Finding, Previous, New and Notes changed fields. `php -l` passed. A screenshot on a mobile browser confirmed two visible events for one finding: one status change from `awaiting` to `follow_up`, and a subsequent notes-only change where status remained `follow_up` and `notes_changed` showed Yes. The history page preserves admin-only access. This confirms the rendered mobile view; it does not prove desktop regression coverage or transactional audit durability.

## Safe verification on the VPS

Run read-only checks without touching the live MUD:

```bash
php -l /var/www/hollowdeep/public/admin/room-investigation-status.php
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/var/lib/hollowdeep/investigation-reviews')
print('Saved findings:', len(json.loads((root/'statuses.json').read_text())))
print('Audit events:', sum(bool(line.strip()) for line in (root/'history.jsonl').open()))
PY
```

For a browser Save test: use an authenticated admin session, change a finding from Awaiting Review to Follow-up Required, enter a unique note, and inspect the browser Network POST to `room-investigation-status.php`. Check its response code and then inspect both storage files. Do **not** post session cookies, CSRF tokens, passwords, private logs or credentials into issues or public chat.

## Private backup and integrity checks (Steps 99U–99W)

On November 7, 2026, the VPS operator created a private audit data archive under `/root/hd-audit-backups/`, outside the web root, using:

```bash
install -d -m 700 /root/hd-audit-backups
tar -czf /root/hd-audit-backups/audit-$(date +%s).tgz -C /var/lib/hollowdeep investigation-reviews
```

The operator reported an approximately 550-byte compressed archive. Status data passed `python3 -m json.tool`, and all four then-recorded audit-history lines parsed as JSON. `tar -tzf` listed the directory and `history.jsonl`, `statuses.lock`, `statuses.json`. This verifies the archive directory listing can be read, **not** a complete restore or all-file extraction. Archives must remain private: do not commit or post investigation data, locks, session data or credentials. For subsequent checks run `gzip -t /root/hd-audit-backups/*.tgz` if there is just one matching archive; for multiple backups, test each separately. Restore only following an explicit recovery plan and an offline verification, never over active storage casually.

On November 7, 2026, the operator additionally ran `gzip -t` successfully (`BACKUP OK`) and streamed `investigation-reviews/statuses.json` out of the archive through `python3 -m json.tool` (`RECOVERY READ OK`). Those checks validate compressed-stream integrity and archived status JSON parseability, **not** a full production restore or point-in-time consistency under concurrent writes. Do not restore over live storage without scheduling an exclusive lock/maintenance procedure.

## Reusable audit health command (Step 99Z)

The operator installed `/usr/local/bin/hd-audit-check` as a root-only executable (`chmod 700`) on November 7, 2026. The command parses `statuses.json` as JSON, parses all nonblank `history.jsonl` lines, then prints `AUDIT HEALTH OK` and the history line count on success. A mobile-terminal check returned:

```text
AUDIT HEALTH OK
4
```

The command is a **read-only syntax and count check**; it does not establish provenance, authenticity, chronological integrity, completeness, or that each audit entry corresponds to a committed status change. It should be run by an authorized administrator with access to the private storage directory. Never publish actual statuses, audit entries, or backup archives.

## Hourly health monitoring and Discord failure alerts (Steps 100–108)

Host-reported setup on November 7, 2026:

- The private `investigation-reviews` directory was verified mode `700` and owned `www-data:www-data`; `statuses.json`, `statuses.lock` and `history.jsonl` were mode `600`, same owner.
- Root-only `/usr/local/bin/hd-audit-check` validates status and history JSON. `/etc/cron.d/hd-audit-health` invokes `/usr/local/bin/hd-audit-alert` at minute zero each hour. `systemctl is-active cron` returned `active`, and a manual run returned `MONITOR OK`. **An actual scheduled execution has not yet been independently verified.**
- Local output appends to `/var/log/hd-audit-health.log` (mode `600`). A weekly `logrotate` policy keeps four compressed rotations, with `su root root`; the dry run no longer reported a directory-permissions error.
- The live Discord webhook is held privately in `/root/.config/hollowdeep/discord-webhook`, owned `root:root` with mode `600`; the directory is mode `700`. The operator checked the webhook using a status-only GET and received HTTP 200. **Never print or commit this URL.**
- The root-only `hd-audit-alert` calls the health checker. On detected failure it posts a generic message to Discord and creates `/root/.config/hollowdeep/audit-failed` only after successful webhook delivery. While that marker exists, repeat alerts are suppressed. A later successful check removes it.
- A deliberately failing `hd-audit-check` placed under a temporary test `PATH` triggered a simulated notification; the operator confirmed seeing the message in Discord `#change-log`. Subsequently the real health check returned `MONITOR OK`. This tests one failure and recovery, **not** scheduled execution, rate-limit resilience, or guaranteed alert delivery.

The test file `/root/hd-test/hd-audit-check` can be deleted after confirmation using `rm -f /root/hd-test/hd-audit-check`; do not change the installed `/usr/local/bin/hd-audit-check`. The source PHP audit append is still nontransactional after the status commit. Automated health checks only validate JSON syntax and cannot detect valid-but-missing/tampered events.

## One-command administrator tool (Step 118)

The reviewed helper is published as [`tools/hd-admin.py`](../tools/hd-admin.py) for **the separate VPS PHP investigation console**. Publishing this file to GitHub does not install or deploy it on the VPS. The tool requires root, uses Python's standard library, and never modifies game source, live room binaries, the MUD process, or the website PHP.

Install on the VPS from an explicitly pinned Git commit (adjust the commit only after review):

```bash
curl -fsSL https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/92ad126576a32cba56e9bc63a5d60124dea9b289/tools/hd-admin.py -o /tmp/hd-admin.py
python3 -m py_compile /tmp/hd-admin.py && install -m 700 /tmp/hd-admin.py /usr/local/bin/hd-admin
hd-admin
```

Commands:

- `hd-admin` or `hd-admin status` — read and parse status/audit JSON, verify private file/directory permissions and ownership consistency, check whether cron is active and whether the hourly alert entry is configured. It **does not** prove scheduled execution or actual Discord delivery.
- `hd-admin backup` — explicitly create a private, mode-600 `.tgz` backup under root-owned `/root/hd-audit-backups`; hold the same exclusive flock on `statuses.lock` used by the PHP status updater while copying. Validate the archive entries and archived status JSON before marking backup complete. It does **not** perform a full restore test.

Keep the real audit records and webhook out of GitHub/Discord. This source tool deliberately contains no webhook URL and performs no GitHub or Discord posting itself; announcements must be explicitly authorized and performed through configured workflows.

### Step 122 — Scheduled cron launch evidence

Version [`ace35a3`](https://github.com/soulkeeper420420/HollowDeep-MUD/commit/ace35a3bd9648d7b2445683e30d03833d9dccf36) extends `hd-admin` to search `/var/log/syslog` and, if needed, `journalctl -u cron` for a **cron CMD** entry invoking `/usr/local/bin/hd-audit-alert`. A cron **RELOAD** alone is not execution evidence. If no matching event appears, the tool displays `not yet observed (or logs unavailable)` without claiming success. A matching CMD proves a scheduled launch, not a successful health-check run or delivered notification.

Upgrade the installed root-only script after reviewing the pinned source:

```bash
curl -fsSL https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/ace35a3bd9648d7b2445683e30d03833d9dccf36/tools/hd-admin.py -o /tmp/hd-admin.py
python3 -m py_compile /tmp/hd-admin.py && cp /usr/local/bin/hd-admin /root/hd-admin.prev && install -m 700 /tmp/hd-admin.py /usr/local/bin/hd-admin
hd-admin
```

No cron modifications, Discord posts, MUD restarts, or changes to live investigation data are made by the upgrade. The new version's **live VPS execution has not yet been confirmed**.

## Step 125 — Operations Overview (host-verified November 7, 2026)

The VPS operator installed `/var/www/hollowdeep/public/admin/operations-overview.php` using `/root/hollowdeep-dev/room-browser/install_step125.py`. The installer backed up the existing Admin Dashboard as `dashboard.php.before-step125-20261107-232947` and added an Operations Overview navigation link. PHP lint passed for both the new page and modified dashboard; the operator **confirmed the admin page loads and displays correctly in a browser**.

The admin-only overview reads existing investigation reports, `statuses.json`, and `history.jsonl` without changing them. It displays Total Findings, Awaiting Review, Reviewed, Follow-up Required, Audit Events, progress percentage/bar, the latest five parsed audit events, a monitoring-information section, and navigation to investigation tools. It intentionally does not read root-only cron logs. This is a browser functional verification, not a comprehensive concurrency or security audit.

Access the page at `https://hollowdeepmud.com/admin/operations-overview.php` with administrator credentials. This PHP installation is on the VPS; **the GitHub documentation does not deploy the PHP source**. The native MUD game and room binaries were not changed or restarted. The hourly schedule's successful post-upgrade run was still pending verification at this point.

## Step 126 — Recent audit history drilldown (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step126.py`, which added a **Finding History** column to the Step 125 Recent Audit Activity table in `/admin/operations-overview.php`. Valid 64-character hexadecimal finding IDs link to `room-investigation-history.php?id=...`; invalid or unavailable IDs render as `Unavailable`. The installer retained a timestamped backup, `operations-overview.php.before-step126-20261107-233545`. Both staged and installed PHP lint checks passed, and the operator confirmed the history link worked in an authenticated browser.

This is a PHP website change performed on the VPS; this GitHub guide is documentation only and does not deploy that PHP source or change the live game.

## Step 127 — Operations Overview audit activity filters (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step127.py`, updating the admin-only `/admin/operations-overview.php` with a GET `activity` selector: **All Activity**, **Status Changes**, and **Notes Changes**. It applies the filter while reading audit events, displays the latest five matching events, and preserves the overall Audit Events card count. The installer retained `operations-overview.php.before-step127-20261107-233821`; PHP lint passed for staged and installed code. The operator confirmed **all three filters and the Step 126 View History link work in the browser**.

This was installed directly on the VPS, not deployed from GitHub. The monitor, private investigation data and native MUD game were not modified by this documentation update.

## Step 128 — Operations Overview audit search (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step128.py`, adding a GET `audit_q` search box to the admin-only `/admin/operations-overview.php`. Searches are capped at 100 characters and match administrator username, finding ID, previous status, or new status; search operates together with Step 127's All/Status/Notes activity filter. The page still shows the latest five matching events while keeping the full audit-event count in its summary card.

The installer retained the timestamped backup `operations-overview.php.before-step128-20261107-234036` and passed staged and installed PHP lint. The operator **confirmed browser search results, search-term retention, combined filtering, and View History links work**. This GitHub guide documents a PHP website change installed separately on the VPS; no private audit events or game files are published.

## Step 129 — Operations Overview audit pagination (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step129.py`, adding GET `audit_page` navigation to the Operations Overview's Recent Audit Activity. The page shows five matching audit events per page, with Previous and Next links that retain the `activity` filter and `audit_q` search. The event-count summary card remains the unfiltered audit total, and Step 126's View History drilldown remains available. The deployed implementation caps requested page values at 1000; the host-reported test involved six events across two pages, not large-scale pagination.

The installer retained the timestamped backup `operations-overview.php.before-step129-20261107-234426` and passed PHP lint on both the staged and installed page. The operator **confirmed both pages, navigation, retained filters/search and View History links in the browser**. This is a VPS-local admin PHP change; the GitHub guide does not deploy code or publish private audit data. No native MUD modifications or restarts occurred.

## Step 130 — Operations Overview direct audit page jump (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step130.py`, adding a **Go to page** numeric form alongside Step 129's Previous/Next navigation in the administrator Operations Overview. The form preserves the GET `activity` filter and `audit_q` query, uses the existing page limit (1 through the available page count, capped at 1000), and retains Step 126's View History links. With six audit events, the operator confirmed navigation between page 1 (five events) and page 2 (one event), filter/search retention, and working history links in the authenticated browser.

The installer retained `operations-overview.php.before-step130-20261107-234638`; both staged and deployed PHP syntax checks passed. Installation occurred on the VPS, not through this GitHub repository. Neither private audit data nor the running native MUD was changed by this documentation update.

## Step 131 — Adjustable Operations Overview audit page size (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step131.py`. The admin-only Operations Overview accepts GET `audit_per_page` values of **5, 10, 25, or 50**, defaulting to five for invalid input. It preserves page size through Previous/Next links and the Go to page form, alongside activity filters, search and View History drilldowns. The installer retained `operations-overview.php.before-step131-20261107-234823` and passed staged and installed PHP lint.

The operator confirmed all four sizes (with six existing audit events), search, activity filters, navigation and View History in the authenticated browser. This documentation does not itself deploy the VPS PHP code or expose private audit records, and no running MUD service or game files were changed.

## Step 132 — Operations Overview audit chronological sorting (host-verified November 7, 2026)

The operator installed `/root/hollowdeep-dev/room-browser/install_step132.py`, adding a GET `audit_sort` selector with **Newest first** (default) and **Oldest first** to the admin-only Operations Overview. Sorting is applied to matching audit entries before pagination and preserves existing activity filters, text search, page size, Previous/Next, direct page jump, and View History links. The operator reported that both sorting orders and pagination/filter/history combinations passed an authenticated browser test with six audit events.

The installer retained `operations-overview.php.before-step132-20261107-234939`; staged and installed PHP lint passed. This feature was installed directly on the VPS. GitHub documentation does not deploy PHP, include private audit records, or alter/restart the live MUD.

## Step 133 — UTC audit date range filtering (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step133.py` to the admin-only Operations Overview. The Recent Audit Activity controls accept optional GET `audit_from` and `audit_to` dates in `YYYY-MM-DD` format, validate actual calendar dates, compare the UTC date portion of audit timestamps, and display an error for a From Date later than the To Date. Both dates are preserved through Previous/Next and Go to page alongside activity filters, search, chronological sort, and page size. Audit Events continues reporting the overall count.

The installer retained `operations-overview.php.before-step133-20261107-235104` and passed PHP lint on the staged and installed page. The operator confirmed date filters, validation, navigation, search, sorting and View History in the browser. This was installed directly on the VPS; this documentation commit does not deploy PHP, include investigation data, or modify or restart the native MUD.

## Step 134 — Reset Operations Overview audit filters (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step134.py` to add a conditional **Reset Filters** link to the administrator Operations Overview. The link appears when audit activity, search, sort, date range, page size, or current page differs from its default, and navigates to `operations-overview.php` without query parameters. Default settings are All Activity, empty search/date fields, Newest first, five events per page and Page 1.

The installer backed up `operations-overview.php.before-step134-20261107-235258`, and staged and deployed PHP syntax checks passed. The operator **confirmed Reset Filters returned the controls to defaults and View History still worked in the browser**. The change was installed directly on the VPS, not deployed by GitHub. No private investigation data or native MUD files were changed.

## Step 135 — Quick UTC audit date presets (host-verified November 7, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step135.py` to add **Today (UTC)**, **Last 7 Days**, and **Last 30 Days** preset links to the administrator Operations Overview. The links compute UTC calendar dates (today, six days earlier or 29 days earlier) and populate both audit date fields. They retain activity filters, text search, chronological sort and page size while resetting pagination to Page 1. The existing Reset Filters link returns to an unrestricted default view.

The installer retained `operations-overview.php.before-step135-20261107-235454`; staged and deployed PHP lint passed. The operator **confirmed all three date presets, preserved search/sort settings and Reset Filters in the browser**. The live PHP change was made on the VPS and is documented here; GitHub publication neither deploys it nor changes private investigation records or the native MUD.

## Step 136 — Full-history audit change breakdown (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step136.py` in the admin-only Operations Overview. It adds read-only counters for **Status Changes Only**, **Notes Changes Only**, and **Status & Notes Changed**. A separate notice accounts for any parsed events with neither flag set. Counters are computed over the entire parsed `history.jsonl` before activity, text, date and pagination filters; they do not reveal private notes. These counters are distinct from the displayed filtered event list.

The installer retained `operations-overview.php.before-step136-20261108-000507`; staged and deployed PHP lint checks passed. The operator confirmed the counters, filter-independent totals and View History links in the browser. This was installed directly on the VPS; GitHub documentation does not deploy PHP or publish audit data, and no native MUD files or processes were changed.

## Step 137 — Audit change-type filtering (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step137.py` in the admin-only Operations Overview. The new GET `change_type` selector supports **All Changes**, **Status Only**, **Notes Only**, and **Status & Notes**. It classifies each audit event by whether `old_status` differs from `new_status` and whether `notes_changed` is true, applying the selection after the Step 136 full-history counters are calculated. The selection persists through Previous/Next, direct page jump, and UTC date presets; Reset Filters returns it to All Changes. The existing activity, text, date, sort and page-size controls remain available.

The installer retained `operations-overview.php.before-step137-20261108-000651`; staged and deployed PHP lint passed. The operator **confirmed all four change-type selections and their interaction with existing controls in the browser**. GitHub publication is documentation only and does not deploy PHP, publish private audit data, or modify/restart the native MUD.

## Step 138 — Clickable audit breakdown cards (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step138.py` to turn the Step 136 full-history summary counters into clickable links in the admin-only Operations Overview. Clicking **Status Changes Only**, **Notes Changes Only**, or **Status & Notes Changed** sets the corresponding Step 137 GET `change_type` filter; the selected card displays “Currently selected.” Links preserve activity, search, chronological sort, page size and UTC date range, and reset pagination to Page 1. The counter totals remain unfiltered, and Reset Filters and View History continue working.

The installer retained `operations-overview.php.before-step138-20261108-000813`; staged and deployed PHP lint passed. The operator confirmed all three cards and their interaction with filters/navigation in the browser. This is a separately installed VPS PHP change; publishing this guide does not deploy PHP, publish private audit records, or modify/restart the native MUD.

## Step 139 — All Audit Events clickable card (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step139.py` to add an **All Audit Events** card alongside the existing three clickable breakdown cards. Clicking this card sets GET `change_type=all` without clearing the activity filter, text search, sort order, page size or UTC date range, and returns the audit list to Page 1. Its count reflects the sum of full-history status-only, notes-only, both-changed and neither-changed events; it is independent of displayed filters. Clicking the other cards continues to select their categories.

The installer backed up `operations-overview.php.before-step139-20261108-000940`; staged and installed PHP lint passed. The operator confirmed all four cards, preserved selections, Reset Filters and View History in the authenticated browser. GitHub publication documents the VPS change but does not deploy PHP, include private audit records, or alter/restart the native MUD.

## Step 140 — Clear only audit date filters (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step140.py` to add a contextual **Clear Dates** link to the admin-only Operations Overview. The link appears when either UTC From Date or To Date is populated; clicking it empties `audit_from` and `audit_to`, retains the existing activity, search, change type, sort and page-size selections, and returns to Page 1. Unlike Reset Filters, Clear Dates does not reset other controls.

The installer retained `operations-overview.php.before-step140-20261108-001115`; staged and deployed PHP lint passed. The operator confirmed Clear Dates with preset and one-sided ranges, preserved controls, existing audit cards, Reset Filters and View History in the authenticated browser. This documentation does not deploy VPS PHP, expose private investigation records, or modify/restart native MUD services.

## Step 141 — Clear only audit text search (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step141.py`, adding a conditional **Clear Search** link beside the Search / Filter button in the administrator Operations Overview. The link is displayed when the GET `audit_q` search term is nonempty. It clears only that search term, preserving activity, change-type, UTC From/To dates, chronological sorting and page size, while resetting audit pagination to Page 1. The existing Clear Dates and Reset Filters controls remain available.

The installer retained `operations-overview.php.before-step141-20261108-001220`; staged and installed PHP lint passed. The operator confirmed the Clear Search behavior, preserved settings and existing cards/drilldowns in the browser. This guide documents the PHP change installed separately on the VPS; GitHub publication does not deploy PHP, reveal private investigation records, or modify/restart the native MUD.

## Step 142 — Clear only audit Change Type (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step142.py` on the admin-only Operations Overview. The contextual **Clear Change Type** link appears when the GET `change_type` selection is not `all`; clicking it restores **All Changes** without clearing activity, audit search, UTC date range, chronological sorting or page-size preferences, and resets audit pagination to Page 1. Existing clickable audit breakdown cards, Clear Dates, Clear Search, Reset Filters and View History remain available.

The installer retained `operations-overview.php.before-step142-20261108-001329`; both staged and deployed PHP lint checks passed. The operator **confirmed the shortcut and preserved controls in the browser**. The live PHP edit took place on the VPS. Publishing this guide does not deploy PHP, expose private investigation data or modify/restart the native MUD.

## Step 143 — Clear only audit Activity filter (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step143.py` to add a contextual **Clear Activity Filter** link to the admin-only Operations Overview. When the GET `activity` choice is Status Changes or Notes Changes, this shortcut switches it back to **All Activity**, retains audit text search, change type, UTC date range, sort order, and page size, and returns to Page 1. Existing Clear Search, Clear Dates, Clear Change Type, Reset Filters, and View History remain available.

The installer retained `operations-overview.php.before-step143-20261108-001441`; staged and installed PHP lint both passed. The operator confirmed the link's behavior with both activity choices and existing controls in an authenticated browser. The VPS PHP change was installed independently of GitHub; publishing this guide does not deploy PHP, expose private investigation records, or modify/restart the live native MUD.

## Step 144 — Clear only audit sort order (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/room-browser/install_step144.py` to add a contextual **Clear Sort** link on the administrator Operations Overview. When GET `audit_sort` is **Oldest first**, the shortcut restores **Newest first**, preserves activity, text search, change type, UTC date range and results-per-page preferences, and resets the audit list to Page 1. Existing Clear Dates, Clear Search, Clear Change Type, Clear Activity Filter, Reset Filters and View History remain available.

The installer retained `operations-overview.php.before-step144-20261108-001632`; staged and installed PHP lint both passed. The operator confirmed Clear Sort, retained selections, and existing controls in an authenticated browser. GitHub publication documents separately installed VPS PHP; it does not deploy PHP, publish private investigation records, or change/restart native MUD services.

## World Builder Studio v1 — visual room exploration and private drafts (host-verified November 8, 2026)

The VPS operator installed `/root/hollowdeep-dev/world-studio/install_v1.py`, creating admin-only `/admin/world-builder-studio.php` at `/var/www/hollowdeep/public/admin/world-builder-studio.php`. PHP lint passed for the staged and deployed page. It was a new page, so no previous-version PHP backup was needed.

**Features:** visual schematic SVG map of up to 36 rooms per page with detected same-page connections; room ID/name/description search; zone filtering where known snapshot fields supply zone labels; room inspector with detected exits; and direct links to existing Room Browser, Connection Inspector, Investigation Queue and Investigation Dashboard. Authentication uses the existing PHP `require_admin()` bootstrap. This is a schematic connectivity visualization, **not** geographic/world-coordinate mapping. Snapshot field extraction is schema-tolerant but may omit unsupported fields.

**Private builder drafts:** proposed name, description, exit-design notes and builder notes are written to standalone, per-room JSON draft files under `/var/lib/hollowdeep/world-studio/drafts/` (www-data-owned, mode 0700 directory, 0600 files). Draft saves require a valid admin session and session CSRF token, validate known snapshot room IDs and field lengths, use an exclusive lock and same-directory temporary-file rename, and redirect after saving. Drafts are **not** applied to game data or investigation records. The initial installer created only the admin PHP page and the private drafts directory, with no native Mordor engine/world edits or restarts.

**Verification:** The operator reported that the full browser acceptance check passed: map node selection, room 1508 search, zone browsing where populated, draft save/refresh persistence, and investigation links. This is a functional browser test, not a complete security review or proof that every snapshot's fields are normalized perfectly. The GitHub publication is documentation only; it does not deploy PHP or publish private draft data.

## World Builder Intelligence v2 — read-only connection graph and draft comparison (host-verified November 8, 2026)

The operator installed `/var/www/hollowdeep/public/admin/world-builder-intelligence.php`, separate from the existing World Builder Studio v1 editor. A terminal run reported successful PHP lint of the staged file `/tmp/hollowdeep-world-intelligence-v2.php` and installed file, and the operator confirmed the v2 browser acceptance tests passed.

**New features:** read-only scan of existing numeric room JSON snapshots (maximum 12,000 files using the v1-compatible, schema-tolerant name/zone/description/exit parser); world summary counts for detected exits, missing destination snapshots and exits with no detected reciprocal link; room-ID selector; clickable SVG neighborhood graph up to 25 rooms and two links from the selected room; incoming and outgoing exit listings; v1 private draft inventory and side-by-side comparison of current name/description against proposed name/description, plus exit-design and builder notes; links to the v1 editor, existing Connection Inspector, Investigation Queue and Investigation Dashboard.

**Interpretation:** this graph is schematic, not geographical. Exit statistics are derived from supported snapshot fields and can differ from the established world-connection report. A missing reciprocal link can be intentional and is not automatically an error. Drafts are **read only in v2**, and draft comparisons are proposals, not deployed edits. This release neither reads nor writes native MUD room binaries.

**Verification/scope:** the operator reported that summary statistics, room 1508 and map navigation, incoming/outgoing connections, available draft comparisons and investigation links worked in the authenticated browser. This is a functional check, not an exhaustive parser or security audit. Installation created a separate PHP admin page; no live game data or running MUD service was changed. GitHub publication records verified VPS behavior but does not deploy PHP or publish private draft contents.

## World Builder Studio v3 — structured proposals and review workflow (host-verified November 8, 2026)

The VPS operator installed `/root/install_hollowdeep_world_builder_v3.sh`, creating the separate admin-only PHP page `/admin/world-builder-review.php` at `/var/www/hollowdeep/public/admin/world-builder-review.php`. Staged and installed PHP lint both passed. The installer reported a new page with no preceding v3 PHP version to back up. The operator confirmed all v3 browser acceptance tests passed.

**Features:** proposal editor for known snapshot rooms; proposed name, description and zone; structured exit proposals entered as `direction:destination` per line; syntax validation, duplicate-direction detection and destination-exists checks against numeric room JSON snapshots; private, per-room proposal files with Draft and Ready for Review statuses; zone-based proposal summary and filtered change-review queue; v1/v2 navigation and existing investigation links. The review status is administrative only, not an approval or deployment.

**Safety and scope:** v3 proposals are stored separately under `/var/lib/hollowdeep/world-studio/proposals/`, owned by `www-data` with a private 0700 directory and 0600 individual JSON files. An authenticated admin session, session CSRF token, input-length checks, file lock and same-directory temporary file rename protect the v3 save workflow. Invalid structured exits are rejected rather than overwriting a saved proposal. Empty proposed exit text means no exit entries proposed; it does **not** remove existing game exits. This is a browser functional verification, not an exhaustive security audit, native Mordor compatibility test or guarantee that exit topology is sound.

The installer did not edit live MUD room binaries, source, snapshots or investigation records and did not restart the game. GitHub publishing records the operator-verified VPS deployment; it does not deploy PHP or publish any private proposal contents.

## World Builder Studio v4 — read-only change-package validation and manifest (host-verified November 8, 2026)

The VPS operator installed `/root/install_hollowdeep_world_builder_v4.sh`, creating the separate admin-only `/admin/world-builder-packages.php` page at `/var/www/hollowdeep/public/admin/world-builder-packages.php`. Staged and deployed PHP syntax checks passed, and the operator reported that all v4 browser acceptance tests passed. It was a new page with no prior v4 PHP backup required.

**Features:** read-only scan of v3 proposal records under `/var/lib/hollowdeep/world-studio/proposals/`; package counters for all proposals, drafts, records with warnings, records ready for review without detected warnings, and invalid/skipped files; checks for missing source snapshots, recorded baseline name/zone drift, invalid workflow statuses, malformed or inconsistent exit text/structured data, missing destination snapshots and dependencies on other proposed rooms. Zone and review-state filters provide a cross-room change-review queue with links back to the v3 proposal editor. The administrator can download a JSON **review manifest** containing IDs, workflow statuses, proposed zones, exit destinations, dependencies and warnings, not full builder notes or descriptions. Export is generated on demand and is not saved server-side.

**Limitations:** 'ready without detected warnings' is not game-engine compatibility certification, human approval or permission to deploy. v3 does not record full source snapshot hashes, so complete drift detection is not possible. An exit to an existing snapshot can still violate native MUD constraints. Exports may contain private planning metadata and should be kept private. Neither viewing nor exporting alters proposals, native game files, investigation records, or MUD services.

**Verification:** The operator confirmed the package counters, warnings and dependencies when applicable, zone/review filtering, links to v3, and JSON manifest download through authenticated browser testing. This is a functional browser check rather than a security audit or deployability assessment. GitHub publication documents the independently installed VPS PHP change and includes no private proposal contents.

## World Builder Studio v5 — read-only change impact analyzer (host-verified November 8, 2026)

The VPS operator installed `/root/install_hollowdeep_world_builder_v5.sh`, adding the standalone admin-only PHP page `/admin/world-builder-impact.php` at `/var/www/hollowdeep/public/admin/world-builder-impact.php`. Both staged and deployed PHP syntax checks passed; the installer reported a new page, so no previous v5 page backup was needed. The operator reported that **all v5 browser verification tests passed**.

**Features:** read-only, schema-tolerant scan of numeric room JSON snapshots and private v3 proposal metadata; a clickable, schematic two-hop neighborhood map with at most 25 rooms, including a visual indicator for neighboring rooms with proposals; per-room incoming and outgoing exit lists; a comparison table showing detected existing destinations against explicit proposed exit entries (omitted proposals **do not** mean deletion); risk notices for missing current or proposed destination snapshots, self-loops, high connection count, proposal baseline name/zone drift, missing Ready for Review status and links to other proposed rooms; cross-proposal dependency links and a manual impact review checklist. The analyzer offers navigation to existing v1–v4 builder tools and the investigation queue.

**Safety and interpretation:** v5 reads snapshots and proposal records but writes neither. The room graph is schematic, not geographical or a simulation of a modified world. The heuristics are advisory, not a completeness proof, human approval, native Mordor file compatibility certification or deployment authorization. No source, native room binaries, live MUD processes, investigation data or private proposals were modified by this install. GitHub publication records the verified VPS deployment but does not deploy PHP or publish private data.

## Live GM Console v1 — read-only operations monitoring (host-verified November 8, 2026)

The VPS operator installed `/root/install_hollowdeep_gm_console_v1.sh`, creating a separate authenticated, administrator-only PHP dashboard at `/var/www/hollowdeep/public/admin/live-gm-console.php` (`/admin/live-gm-console.php`). Staged and installed PHP lint passed. This was a new page, with no previous version to back up. The operator **confirmed all v1 browser acceptance tests passed**.

**Capabilities:** host uptime, system load, available/total memory and filesystem capacity from read-only Linux and PHP interfaces; heuristic inspection of accessible Linux process **names only** for possible MUD processes (no command-line arguments, credentials or environment); count of numeric room JSON snapshots; availability and last-modified timestamp of the existing world connection report; private builder draft/proposal counts; and a recent investigation audit activity summary containing timestamps, old/new review statuses and whether notes changed, without revealing note text. Navigation links connect to the Operations Overview, investigations and World Builder v1–v5.

**Interpretation and security boundaries:** the process-name check does not prove the game is running or accepting logins. Snapshot counts and report readability are not authoritative gameplay health. The investigation summary may be partial (up to 50,000 scanned audit lines), and no native game integration or player presence was established. There is **no** shell command endpoint, native GM command execution, player edit, game restart, or mutation of world/player data. Admin authentication uses the existing `require_admin()` bootstrap. The operator tested page health metrics, process-detection display, world monitoring, audit summary, link navigation and absence of command controls in an authenticated browser; this is a functional test, not a comprehensive security audit. GitHub publication documents the independently installed VPS PHP page, but does not deploy PHP or expose private records.

## Live GM Console v2 — systemd-backed game process and TCP monitoring (host-verified November 2026)

The VPS operator installed `/root/install_hollowdeep_gm_console_v2.sh`, deploying the separate authenticated PHP dashboard `/admin/live-gm-console-v2.php`, the restricted collector `/usr/local/libexec/hollowdeep-gm-monitor.py`, and `hollowdeep-gm-monitor.service` plus the enabled `hollowdeep-gm-monitor.timer`. The operator reported that the PHP staged/installed syntax checks passed, the timer was active, the collector wrote its snapshot, and **all v2 authenticated browser acceptance tests passed**, including monitoring freshness and navigation.

**Verified native game integration:** `hollowdeep.service` was observed active with `MainPID=717` at the time of installation; executable `frp.new` from the original Mordor 3.00 runtime; process-owned TCP listener on port **4040**. The first collector output observed **1 established TCP connection**. These PID and connection values are point-in-time observations and may change. The earlier systemd inspection identified `User=hollowdeep`, `WorkingDirectory=/srv/hollowdeep/world`, and executable `/srv/hollowdeep/world/src_3.00/frp.new`.

**Architecture:** a separate root-run one-shot monitor examines `systemctl show`, selected `/proc` process metadata, and process-owned socket inode matches against `/proc/net/tcp*` for local port 4040. It writes an atomic sanitized snapshot to `/var/lib/hollowdeep/gm-monitor/status.json` under root ownership with `www-data` group read permission; the web page reads only this snapshot and treats older-than-three-minute data as stale. The timer collects roughly once a minute. It has no game login probe and sends no command to the native game.

**Limits and safety:** a detected listener proves a bound socket, not successful login or overall gameplay health. Established TCP connections include unauthenticated clients and must **not** be represented as online player counts. Authenticated player presence remains **not integrated**, and GM command controls remain disabled. The installer reports no native game files changed and no `hollowdeep.service` restart. It did install and enable its own dedicated systemd monitoring units. As with prior steps, publishing this documentation does not deploy the VPS PHP or collector and includes no player data, private credentials or session content.

**Future integration prerequisite:** establish how Mordor marks a connection as successfully logged in, and whether an existing safe status interface exists, before implementing authenticated session counts or names. Treat source inspection separately from game changes; avoid exposing character content or internal pointers through the PHP website.

## Live GM Console v3 — native authenticated player presence (operator-verified, November 8, 2026)

**Production acceptance:** The operator installed the isolated GNU89/ELF32 native Mordor build on the Ubuntu VPS and verified the `/admin/live-gm-console-v3.php` authenticated dashboard. The activation script reported `hollowdeep.service` active, valid native presence JSON, an active monitoring bridge, and authenticated count **0** immediately following restart. A subsequent authenticated browser screenshot displayed **1** online player and **1** established TCP connection during a real character login. A further screenshot after logout displayed **0** online players, **0** established TCP connections, and the game service still **active**. This demonstrates the login/logout count transition in production; it is not a claim of exhaustive concurrency, performance, or security testing.

**Native mechanism:** In the Mordor 3.00 engine, the `Ply[]` entry may exist during login while `ply->fd == -1`. Both existing-character login and new-character creation set `ply->fd = fd` before entering command handling. A periodically invoked publisher in `io.c` counts sessions for which `Ply[i].io != NULL && Ply[i].ply != NULL && Ply[i].ply->fd == i`. Do **not** use `Numplayers` as an authenticated count: it is incremented when a connection reaches the login prompt. Do **not** infer authenticated presence from an established TCP connection or from `PSECOK`, which is cleared during character initialization.

**Data flow and boundaries:**
- Native `frp.new` writes a count-only `/var/lib/hollowdeep/gm-presence/status.json` roughly every 30 seconds through a private temporary file and same-filesystem atomic rename. Fields: `schema: hollowdeep-presence-v3`, `timestamp_unix`, `authenticated_players`. No player names, addresses, credentials, commands or character records are emitted.
- The native directory is `hollowdeep:hollowdeep`, mode `0700`; snapshot files are mode `0600`. The root-run `/usr/local/libexec/hollowdeep-gm-monitor.py` collector validates native file ownership, regular-file status, size, schema, count type and timestamp freshness, then adds `native_presence_v3` to the existing v2 monitoring snapshot under `/var/lib/hollowdeep/gm-monitor/status.json`. A missing, invalid or stale native snapshot yields `available=false` and `authenticated_players=null`, **not zero**.
- The admin-only `/admin/live-gm-console-v3.php` page checks monitoring freshness, displays native authenticated count separately from TCP connections, and does not expose command execution.
- Service sandbox keeps `ProtectSystem=strict`. A systemd override `/etc/systemd/system/hollowdeep.service.d/90-gm-presence-v3.conf` grants `ReadWritePaths=/srv/hollowdeep/world /var/lib/hollowdeep/gm-presence`. The first activation failed because the service previously allowed writing only to `/srv/hollowdeep/world`; its automatic rollback restored the original executable and restarted the service. Adding the narrow writable path, validating the unit and reactivating resolved the missing snapshot. This override is required for subsequent native starts.

**Build and release controls:** Offline source and binary were staged in `/root/hollowdeep-dev/gm-presence-v3-20261108-020814`, with a root-only release bundle at `/root/hollowdeep-dev/releases/gm-presence-v3`. Original executable SHA-256: `0aaca56032fe1454b4cab4e2cd7a3ac2bbb2e5c03632b825bf0ae395c50f40ad`; activated v3 candidate SHA-256: `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`. Offline counting harness passed six simulated states and 100 valid JSON samples. Following removal of explicit `fsync()` from the single-threaded game loop, the sample median was 1.378 ms, p95 1.526 ms and maximum 1.808 ms; samples include process startup and do **not** establish live gameplay latency. Game-loop filesystem writes can still block.

**Operations and rollback:** Deployment script on the VPS: `/root/finish_hollowdeep_console_v3.sh`; preserved original executable: `/root/hollowdeep-dev/releases/gm-presence-v3/frp.original`. A production rollback requires coordinated player logout and another game restart. To troubleshoot unavailable counts, inspect `hollowdeep.service`, the service sandbox `ReadWritePaths`, native snapshot freshness/permissions, and the `hollowdeep-gm-monitor.service` output. Do not remove the override during normal v3 operation. These paths describe the operator's separate VPS environment; **this GitHub documentation commit does not deploy the native binary, systemd units or PHP page**. Do not upload private snapshots, saved characters or live server secrets to the repository.

## Live GM Console v4 — read-only native GM command reference (November 8, 2026)

**Deployment reported by operator:** Installed `/admin/live-gm-console-v4.php` on the separate Ubuntu VPS. The initial installer extracted 59 native `dm_*` and `hd_staff_*` function definitions across eight C source files and organized them into five preliminary categories; staged and installed PHP lint passed and `hollowdeep.service` remained active without a restart. The original 59-function catalog remains present in the Stage 2 build.

**Registry source:** In the native Mordor source, `global.c` defines `cmdlist[]` at lines 166–488. A first diagnostic missed its initializer and reported zero records; a corrected scanner extracted 320 registration lines. The Stage 2 installer isolated 54 `*`-prefixed GM registrations/aliases mapping to 49 distinct handlers. Examples directly verified in the extracted registry are `*teleport`/`*t` → `dm_teleport` (command 101), `*users` → `dm_users` (111), `*shutdown` → `dm_shutdown` (114), `*force`/`*f` → `dm_force` (115), `*set` → `dm_set` (120), `*silence` → `dm_silence` (128), and `*attack` → `dm_attack` (143). Command name, command number, handler and `global.c` source line now appear in the admin-only read-only catalog. A mobile screenshot explicitly verified display of `*teleport`, `dm_teleport`, ID 101 and `global.c:431`, the native authorization notice and “Execution: Disabled”. This establishes visible rendering of that card, **not yet** search/filter behavior, all other cards, or a complete authorization audit.

**Authorization caveats:** `command1.c` checks `hd_native_command_allowed(player, cmdno)` before dispatch for `*` commands and subsequently checks `hd_staff_blocks_command`. Some `dm*.c` handlers additionally enforce `ply_ptr->class >= CARETAKER`. `hollowdeep_staff.c` has a separate role/rank model: player rank 0, moderator and implementor rank 1, administrator rank 2, owner rank 3. `hd_staff_authorize_action()` checks rank and audit storage only for supported action names; it is **not** automatically a universal permission guard for all `dm_*` handlers. The web UI must continue to label effective per-command staff requirements **unverified** until each handler and `hd_native_command_allowed` are audited. A native role ID is not a native class level.

**Safety and recovery:** The console is administrator-authenticated PHP and contains a static embedded command-reference snapshot. There is no generic web-to-MUD command executor, and the installation made no native game source, character or world modifications. The operator reported a successful staged/install `php -l`, an active game service, and zero MUD restarts. Stage 2 backup: `/root/hollowdeep-dev/gm-v4/backups/live-gm-console-v4-before-map-20261108-031504.php`. Private source-derived inventories were kept under `/root/hollowdeep-dev/gm-v4/`. This GitHub commit documents the VPS change only; it does not deploy PHP or native code. Next validation: test command search, category filtering, `*shutdown` rendering, and preservation of the original catalog in the browser. Do not publish private player records, audit data, or secrets.

## Live GM Console v4 Stage 3 — verified native dispatcher permissions (operator-installed, November 8, 2026)

**Source-derived rule:** `hd_native_command_allowed(creature *player, int number)` at `hollowdeep_help.c:20–30` first rejects non-player objects and native character classes below `CARETAKER`. For registered `*` command IDs 101–149 the default gate is native `CARETAKER`; command IDs 106, 119, 129, 141, 144, 145, 146 and 148 require native `DM`; ID 113 (`*flushrooms`) requires native `DM`, nonempty `DMNAME2`, and an exact name match to `DMNAME2`. An empty `DMNAME2` denies ID 113. These are **dispatcher gates**, not full effective authorization conclusions.

The dispatcher in `command1.c:622–630` applies this check for `*` commands and then `hd_staff_blocks_command` before invoking the handler. Handler-local checks and indirect guards must still be evaluated individually. Separately, `hollowdeep_staff.c` assigns player rank 0, moderator and implementor rank 1, administrator rank 2, and owner rank 3, but those role ranks do not substitute for native `CARETAKER`/`DM` character classes. `hd_staff_authorize_action` is specifically scoped to supported audited action names and must not be described as protecting all GM commands.

**Stage 3 scanner and review:** The operator audited 54 registrations/49 distinct handlers, initially found 47 handler bodies and flagged 18 high-impact handler groups for priority manual review. Follow-up source search located the two scanner misses, `dm_finger` in `dm3.c:754` and `dm_list` in `dm3.c:823`. The scanner is not a complete C parser; identified checks are evidence candidates, not proof of every runtime control flow.

**Stage 3 installation:** The operator ran `/root/upgrade_hollowdeep_gm_v4_permissions.sh`. The installer checked the reviewed gate source against expected strings, validated all 54 registered command records, staged and atomically installed the administrator PHP page, and passed all reported `php -l` checks. It reported keeping 49 distinct handlers and the 59-function reference, with command execution still disabled. `hollowdeep.service` was active, no native modifications and no MUD restart occurred. Production rollback backup: `/root/hollowdeep-dev/gm-v4/backups/live-gm-console-v4-before-permissions-20261108-032231.php`.

**Verification status:** Stage 3 installation and PHP lint are operator-confirmed. A **Stage 3 browser screenshot and per-command label/search tests have not yet been supplied**. Earlier Stage 2 browser evidence confirmed only the `*teleport` command card. Do not mark Stage 3 browser acceptance complete. Suggested spot checks include `*teleport` and `*shutdown` → native `CARETAKER`; `*perm` and `*auth` → native `DM`; `*flushrooms` → native `DM` plus configured `DMNAME2` identity; and continued “Execution: Disabled” rendering. This documentation is not the deployed PHP source and does not activate web GM execution.

## Live GM Moderation Center v4 — Stage 4 (operator-installed; partial mobile browser verification, November 8, 2026)

**Scope:** A separate administrator-only, read-only native moderation reference at `/admin/gm-moderation-v4.php` on the Ubuntu VPS. It links back to the existing v4 command catalog and v3 player dashboard and documents native staff permissions, target protections, audit behavior, and requirements for any future live moderation bridge. It does **not** provide buttons, POST endpoints, shell invocation, or a web-to-game command channel for mute, unmute, kick, announce, grant, or revoke.

**Source-grounded moderation findings (`hollowdeep_staff.c`):** `hstaff whoami` requires a valid loaded staff-state identity, `hstaff list` requires moderator rank, `hstaff audit` requires administrator rank, and `hstaff grant/revoke` requires administrator rank plus existing saved-character, hierarchy, founder and self-change restrictions (lines 473–542). `hmoderate announce`, `mute`, `unmute`, and `kick` require moderator rank (lines 563–642); announce requires a validated 1–180-character printable ASCII message and staff-chat permission; mute accepts 1–1440 minutes (default 10) and requires an online saved-character target; kick likewise requires an online target; unmute can target an offline saved character with a stored active mute. Moderation rejects self-targets and targets with equal/higher staff rank, and non-owner staff cannot moderate online native `CARETAKER` characters. Separate native class gates and HollowDeep staff-role ranks should not be conflated.

**Audit interpretation:** `audit_action()` appends an audit entry to in-memory staff state and calls `save_staff(state)` (lines 344–360). For persistent mute/unmute and role changes, the state is mutated before this audit/save call. For announce/kick, audit/save occurs before broadcast or disconnect. This is an attempted audit-before-effect ordering; a saved request audit does **not** confirm a later effect completed, and the inspected excerpts do not prove crash durability, transactional behavior with side effects, or idempotent retries. Native staff audit entries are private and must not be included in GitHub.

**Installation and acceptance evidence:** The operator ran `/root/install_hollowdeep_gm_moderation_v4.sh` and reported that staged, temporary and installed PHP each passed `php -l`, with `hollowdeep.service` active. The installer reported no changes to the v4 catalog or native game and no MUD restart. An authenticated mobile screenshot showed the native operations page presenting separate readable cards for `hstaff whoami` (valid staff-state identity), `hstaff list` (Moderator), and `hstaff audit` (Administrator). Thus **initial mobile rendering was verified**; the screenshot did not show every operation, full-page navigation, cross-browser behavior, or exhaustively establish absence of actions across other pages. No live moderation action was exercised.

**Future bridge gate:** Before enabling any web-triggered moderation, design an explicit allowlisted native RPC protocol, bound to a narrowly privileged local service, with native staff-identity authorization, target validation and protected-target checks at time of execution, authenticated request origin, CSRF protection in the admin UI, request/result correlation, audit outcome semantics, replay prevention and defined timeouts. Avoid arbitrary command passthrough and automatic retries of uncertain effects. No such bridge is deployed as part of Stage 4.

GitHub publication documents the independent VPS deployment only; it does not upload or activate the VPS PHP code, systemd units, native binaries, staff records, or any private player/audit data.

## GM Stage 5A/5B — bridge readiness and isolated protocol (operator-tested, November 8, 2026)

**No live bridge has been deployed.** Stage 5A read the native C engine, web authentication function names, host service sandbox and account ownership. The native staff authorization path `actor_role` requires a connected, valid player and a live file descriptor; a PHP `require_admin()` session is not, by itself, a native staff identity. The web app's bootstrap exposes `session_begin()`, `csrf()` and `require_admin()`. `hollowdeep.service` runs as `hollowdeep:hollowdeep`, with `ProtectSystem=strict`, `PrivateTmp=yes`, `NoNewPrivileges=yes`, no `RuntimeDirectory` configured and a restricted `ReadWritePaths` set. PHP-FPM/nginx workers include `www-data`; the eventual socket access path and native identity binding still need independent design and verification.

**Production executable reconciliation:** Reading `/proc/<MainPID>/exe` and hashing the running binary yielded SHA-256 `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`, identical to the recorded native player-presence v3 executable. The live `/srv/hollowdeep/world/src_3.00/io.c` contains none of the expected `hd_presence_snapshot`, `hollowdeep-presence-v3`, `authenticated_players`, or `gm-presence` markers. The prior offline staged source `/root/hollowdeep-dev/gm-presence-v3-20261108-020814/source/io.c` contains all four. **Do not rebuild from the older live source tree** without first reconciling it with the staged v3 release. The staged source is a likely baseline candidate, not independently proven to correspond byte-for-byte to the deployed binary; a full manifest and build provenance check are still needed.

**Live health check:** The presence snapshot remained schema-valid and fresh (18.1 seconds old at the operator's check), private mode `0600`, and `hollowdeep.service` remained active.

**Isolated bridge tests:** Stage 5B ran a disposable Python Unix-domain socket mock in a private temporary directory, with a transient in-memory replay set and local peer-UID equality check. All six specified cases passed: read-only capabilities was allowed, a reused request ID was rejected, proposed `mute` and `*shutdown` operations were denied, an injected actor field was rejected as malformed, and a missing request ID was rejected. The test socket was removed. The prototype made **no connection to the native game or PHP site**, deployed no units, created no native endpoint, altered no game source, executed no GM commands, and did not restart the game. The mock's same-UID check is **not** proof of web administrator identity, native GM rank, persistent replay safety, audit durability, or production transport security.

**Next release gate:** Freeze and compare the complete staged v3 source and release manifest; establish reproducible build provenance; separately assess systemd socket restrictions and ownership. Only then prototype a native-process-owned, **read-only** `capabilities` operation, with explicit web-to-native identity binding, mutual request authentication and controlled authorization. Do not enable arbitrary command strings, live moderation, or speculative automatic retries.

## GM Stage 5C — native v3 baseline preservation (operator-verified, November 8, 2026)

The operator ran `/root/hollowdeep_v5c_baseline.sh` on the separate production VPS without changing the MUD service, the website, or any game files. The executable read from `/proc/<MainPID>/exe` **and** the retained release binary `/root/hollowdeep-dev/releases/gm-presence-v3/frp.v3` each matched the previously recorded v3 SHA-256: `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`.

The staged tree `/root/hollowdeep-dev/gm-presence-v3-20261108-020814/source` had 133 regular source-tree files, including the v3 player-presence publisher markers. The code inventory of staged and live trees each contained 74 `.c`, `.h`, `.S`, or Makefile-named files; **only `io.c` differed** in that inventory. The live `/srv/hollowdeep/world/src_3.00/io.c` lacks the v3 publisher present in staged `io.c`. This is a code-inventory comparison rather than an all-file identity check; it does not prove a bit-for-bit reproducible compilation or that the running executable's entire source provenance is established.

A private, root-only snapshot was preserved at `/root/hollowdeep-dev/gm-v5/baselines/v3-20261108-034207/v3-source-baseline.tar.gz`, with source manifest at `/root/hollowdeep-dev/gm-v5/baselines/v3-20261108-034207/manifest.json`. Archive SHA-256: `791debfa2f347ba729c66bad3449f1e3748db7e92541dd4d169c7baf2da87084`. **Keep this private baseline and the known-good release executable intact; do not compile the older live source tree over v3**. Build provenance remains a separate pre-deployment validation requirement. The production service remained active, no restart occurred, and no native or web GM action channel was deployed.

## GM Stage 5D — isolated ELF32 Unix-domain socket prototype (operator-tested, November 8, 2026)

The operator compiled a standalone `gcc -m32` C socket server prototype at `/root/hollowdeep-dev/gm-v5/native-prototype/bridge_stub`; the `file` and ELF-header checks confirmed a 32-bit Intel 80386 ELF PIE executable. A private `0600` Unix-domain socket served eight local test messages, and all eight checks passed: read-only capabilities allowed; reused request ID rejected; `mute` and `*shutdown` denied; extra `actor` identity field, absent ID, boolean protocol-version field and oversized frame rejected. The test socket was removed. The operator reported `hollowdeep.service` active, no restart, no production website or game changes, and no native GM commands executed.

**Scope limitations:** This is an isolated, non-deployed server stub rather than a bridge linked into Mordor's game loop. Its peer-UID equality check demonstrates only local credential retrieval, not website administrator authentication or in-game GM authorization. The strict canonical request-format parser is test-specific rather than a complete JSON parser. Its replay cache is transient and in-process and has no crash-persistence or bounded production lifecycle design. It does not establish durability, timeouts under full game load, cross-UID access, web-to-native identity binding, or permission safety for any live action. None of the eight tests constitutes a production game integration test. Next: inspect the preserved v3 `io.c` loop and Makefile in a separate development copy before proposing a non-blocking native read-only interface. Do not overwrite the live game or replace the known-good v3 source baseline.

## Publishing policy

Publish **reviewed and tested** code, guides and changelogs to the `soulkeeper420420/HollowDeep-MUD` GitHub repository. For this separate VPS console, obtain a reviewed, sanitized copy of the actual deployed PHP/installer files before publishing source. Do not infer that the current GitHub repository's Sites/Node frontend deploys the VPS PHP console.

For release announcements, the intended Discord destination is **#change-log**. A channel name alone does not grant permission to send; use an authorized bot or webhook configured for that channel. Never include the webhook URL or bot token in GitHub. Post release notes with the commit link, verified scope and outstanding issues. Announce unresolved work as investigation status, not a completed release.

Do not publish live MUD room binaries, saved player data, server private settings, credentials or status/audit data.
