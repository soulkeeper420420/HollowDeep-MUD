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

## Publishing policy

Publish **reviewed and tested** code, guides and changelogs to the `soulkeeper420420/HollowDeep-MUD` GitHub repository. For this separate VPS console, obtain a reviewed, sanitized copy of the actual deployed PHP/installer files before publishing source. Do not infer that the current GitHub repository's Sites/Node frontend deploys the VPS PHP console.

For release announcements, the intended Discord destination is **#change-log**. A channel name alone does not grant permission to send; use an authorized bot or webhook configured for that channel. Never include the webhook URL or bot token in GitHub. Post release notes with the commit link, verified scope and outstanding issues. Announce unresolved work as investigation status, not a completed release.

Do not publish live MUD room binaries, saved player data, server private settings, credentials or status/audit data.
