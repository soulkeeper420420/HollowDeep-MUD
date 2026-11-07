# VPS Investigation Console: status and publication guide

> Scope: PHP administrator investigation console on `hollowdeepmud.com`, operated on the Ubuntu 24.04 VPS. This is **separate** from the repository's browser/Sites frontend and native Mordor updater. GitHub publication does not deploy this console.

## Available read-only diagnostics (host-reported, November 7, 2026)

- Room JSON snapshots: `/var/lib/hollowdeep/room-browser/[room_id].json`; reports are generated from snapshots, not live room binaries.
- World connection report: `/var/lib/hollowdeep/room-browser/world-connection-report.json`.
- Incoming exit index: `/var/lib/hollowdeep/room-browser/incoming-exits-index.json`.
- Admin pages: `/admin/world-connections.php`, `/admin/world-connection-inspector.php`, `/admin/room-investigations.php`, `/admin/room-investigation-queue.php`, and `/admin/room-investigation-history.php`.
- Current report: 4,030 rooms, 9,551 valid exits, 12 missing destination exits, 552 one-way exits, 38 isolated rooms and 8 duplicate groups. These are snapshot-analysis findings; they are not instructions to change live room data.
- Room 3470's binary exists but appears unusually short; its missing snapshot merits manual inspection. Do not call the game room corrupted without further proof.

## Review workflow and unresolved audit issue

The queue and endpoint contain forms for statuses `awaiting`, `reviewed`, `follow_up` and notes up to 8,000 bytes. The intended storage is private, outside the webroot:

- `/var/lib/hollowdeep/investigation-reviews/statuses.json`
- `/var/lib/hollowdeep/investigation-reviews/statuses.lock`
- `/var/lib/hollowdeep/investigation-reviews/history.jsonl`

The form POSTs to `/admin/room-investigation-status.php`. Its source uses admin authentication, CSRF validation, finding ID validation against the current report, exclusive file locking, and an atomic status-file rename. The audit append runs only when status or notes actually change.

**Not verified / current blocker:** During checks on November 7, 2026, `statuses.json` remained a three-byte empty object (`{}`) with zero saved findings, and `history.jsonl` remained zero bytes with zero audit events, even after a reported browser Save and redirect. The form markup, Nginx document root (`/var/www/hollowdeep/public`), file permissions, PHP syntax, and www-data workers were checked. A browser redirect does not prove persistence. Do not announce the review/audit functionality as fixed.

The current endpoint appends an audit event **before** the status-file replacement, so a later storage failure could leave an audit entry without a matching committed status. A future reliability patch should address this ordering/transactional limitation after the basic Save issue is diagnosed.

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

## Publishing policy

Publish **reviewed and tested** code, guides and changelogs to the `soulkeeper420420/HollowDeep-MUD` GitHub repository. For this separate VPS console, obtain a reviewed, sanitized copy of the actual deployed PHP/installer files before publishing source. Do not infer that the current GitHub repository's Sites/Node frontend deploys the VPS PHP console.

For release announcements, the intended Discord destination is **#change-log**. A channel name alone does not grant permission to send; use an authorized bot or webhook configured for that channel. Never include the webhook URL or bot token in GitHub. Post release notes with the commit link, verified scope and outstanding issues. Announce unresolved work as investigation status, not a completed release.

Do not publish live MUD room binaries, saved player data, server private settings, credentials or status/audit data.
