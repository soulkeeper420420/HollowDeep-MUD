# HollowDeep PHP website previews (V1–V6)

**Status: November 9, 2026.** This document records the separately deployed PHP previews on the HollowDeep web host. These previews are **not** the Next.js/Vinext site in this repository and are not a live-game deployment.

## Current preview routes

Base public origin: `https://www.hollowdeepmud.com`

| Version | Preview | What is included | Verified evidence |
| --- | --- | --- | --- |
| V1 | `/hollowdeep-preview/` | Homepage, player guide, Chronicles, updates | Four HTTP 200 responses, PHP lint passed |
| V2 | `/hollowdeep-preview-v2/` | Mobile-facing landing, player portal, browser-local Chronicle planner | Four HTTP 200 responses, PHP lint passed |
| V3 | `/hollowdeep-preview-v3/` | Adventurer's Tavern, Dungeon Delve, quiz, dice, searchable Codex | Six PHP pages and three assets HTTP 200, PHP lint passed |
| V4 | `/hollowdeep-preview-v4/` | Daily Chronicle, Rune Memory, Tavern Passport stamps, mobile quick navigation | Ten HTTP 200 responses, PHP lint passed; **seven browser functional tests passed, zero failed** |
| V5 | `/hollowdeep-preview-v5/` | Adventure Hub, activity links, summary of locally saved stamps/plans, surprise activity | Eleven HTTP 200 responses, PHP lint passed; **ten browser functional checks passed, zero failed** |
| V6 | `/hollowdeep-preview-v6/` | Start Here onboarding, simplified mobile navigation, clear preview notice | **Eleven HTTP 200 responses and PHP lint passed; nine pages and sixteen internal targets passed read-only link audit, zero failures**; manual mobile/browser review pending |

The V4 browser test page was deployed separately at `/hollowdeep-preview-v4-qa/index.html`; the owner supplied a screenshot showing 7 passed and 0 failed. The V5 browser QA page at `/hollowdeep-preview-v5-qa/index.html` was also opened in-browser, and the owner supplied a screenshot showing **10 passed, 0 failed**. These tests cover the supplied QA checks, not exhaustive visual usability or a live game integration. HTTP 200 alone is a delivery check, not proof of JavaScript behavior.

## V6 entry points

- Homepage: `/hollowdeep-preview-v6/index.php`
- Adventure Hub: `/hollowdeep-preview-v6/hub.php`
- Tavern: `/hollowdeep-preview-v6/tavern.php`
- Codex: `/hollowdeep-preview-v6/codex.php`
- Daily Challenge: `/hollowdeep-preview-v6/daily.php`
- Player Portal: `/hollowdeep-preview-v5/portal.php`

- Start Here: `/hollowdeep-preview-v6/start.php`

The local quest planner uses browser localStorage. The Tavern Passport and Daily Chronicle also store activity locally in the browser. **None are real Mordor character data, XP, gold, achievements, or game-server rewards.**

## Deployment boundaries

- The host's PHP previews reside under `/var/www/hollowdeep/public/` in versioned directories. Do not confuse them with the native C engine or the repository's separate web application.
- Previous previews, existing production homepage, administration tools, database, and native game server were reported unchanged by the installation checks.
- These website deployments were not confirmed as the live homepage.
- Browser play needs a separately authenticated TLS WebSocket-to-Telnet bridge; do not represent a static Play page as a live connected client.
- Never publish player saves, private server configuration, database credentials, signing keys, passwords, or production logs.

## Validation before considering promotion

1. Run `php -l` on every PHP file and verify that pages, scripts, and stylesheets respond successfully.
2. The V5 browser QA checks passed (10/10); still perform a manual mobile layout and touch/keyboard usability review. The host did not have Node.js installed during these previews.
3. Exercise keyboard and touch navigation and make sure buttons do not navigate unexpectedly.
4. Ensure that activities do not claim to change the game character or server.
5. Compare source checksums of the old preview before and after installing the new one.
6. Promote to the primary site only with deliberate rollback planning and a separate deployment approval. Do not overwrite the current admin dashboard.

## Work remaining

- Complete the V6 manual mobile usability and accessibility review; the read-only HTTP/link audit already passed 9 pages and 16 link/asset targets, with 0 failures. Correct any visual, touch, or accessibility findings in a separately staged change.
- Organize and publish the PHP source files separately from this guide if they are exported from the server and reviewed for secrets. The code snippets used to install previews are not automatically synchronized to this GitHub repository.
- Prepare a Discord changelog/announcement once V6 is validated for public promotion. A local changelog file does not itself publish to Discord.
- Keep V22 combat-target work on hold until the website milestone is finished.

## November 9, 2026 — Official homepage launch preflight

The owner ran a **read-only** preflight on the Linode web host:

- Current public document root: `/var/www/hollowdeep/public`.
- Current root `index.php`: 89 bytes, root-owned, mode 0644, SHA-256 `89f6478d608b3977d60d003fe11cb4aab2195450411c994d82f044c198587ded`.
- No `index.html` at the public root was reported.
- `nginx -t`: successful.
- Disk: 79 GB volume, ~68 GB available, 9% used.
- The official root URL and V6 preview homepage both returned HTTP 200.
- V6 read-only audit: 9 pages and 16 internal links/assets passed, 0 failures. This is not a visual/mobile usability certification.

**Promotion policy:** No release approval has been given. Keep all existing admin routes, engine, player saves, and database untouched. Prepare a private, checksum-verified rollback backup and staging candidate before modifying the live 89-byte root homepage. Remove preview-only `noindex` and preview messaging **only in a final approved release copy**, not by changing existing previews. Do not change Nginx configuration or restart services during backup preparation. Test the actual launch/rollback route before replacing the root file; a redirect from the homepage to a stable release subdirectory is safer than overwriting unknown root files.

## November 9, 2026 — Safe launch candidate verified

The owner ran the guarded launch-preparation script successfully. A private rollback backup of the original root homepage and V6 source was created and checksummed; its location is retained privately on the host, **not** in this public document. A separate `/hollowdeep-launch-candidate/` directory was staged. All ten PHP source files passed `php -l`; Nginx configuration passed `nginx -t`; twelve candidate page/asset requests returned HTTP 200. The original root `index.php` checksum matched its preflight baseline, the V6 source was unchanged, and no service restarts, admin changes, database writes, or native game operations were performed.

**Release is not approved or completed.** The candidate intentionally retains `noindex,nofollow` metadata and the preview notice. Before launch, manually check the mobile/desktop interface, confirm where the current 89-byte root homepage routes, prepare final production-only metadata/wording changes, and obtain explicit approval before changing the public root. Preserve the private backup and test a rollback after any approved switch. Avoid copying secrets or player data to public repositories.
