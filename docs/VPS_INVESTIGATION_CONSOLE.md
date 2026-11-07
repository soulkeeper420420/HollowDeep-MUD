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

## Publishing policy

Publish **reviewed and tested** code, guides and changelogs to the `soulkeeper420420/HollowDeep-MUD` GitHub repository. For this separate VPS console, obtain a reviewed, sanitized copy of the actual deployed PHP/installer files before publishing source. Do not infer that the current GitHub repository's Sites/Node frontend deploys the VPS PHP console.

For release announcements, the intended Discord destination is **#change-log**. A channel name alone does not grant permission to send; use an authorized bot or webhook configured for that channel. Never include the webhook URL or bot token in GitHub. Post release notes with the commit link, verified scope and outstanding issues. Announce unresolved work as investigation status, not a completed release.

Do not publish live MUD room binaries, saved player data, server private settings, credentials or status/audit data.
