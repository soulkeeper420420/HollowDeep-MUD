# HollowDeep PHP website previews (V1–V5)

**Status: November 9, 2026.** This document records the separately deployed PHP previews on the HollowDeep web host. These previews are **not** the Next.js/Vinext site in this repository and are not a live-game deployment.

## Current preview routes

Base public origin: `https://www.hollowdeepmud.com`

| Version | Preview | What is included | Verified evidence |
| --- | --- | --- | --- |
| V1 | `/hollowdeep-preview/` | Homepage, player guide, Chronicles, updates | Four HTTP 200 responses, PHP lint passed |
| V2 | `/hollowdeep-preview-v2/` | Mobile-facing landing, player portal, browser-local Chronicle planner | Four HTTP 200 responses, PHP lint passed |
| V3 | `/hollowdeep-preview-v3/` | Adventurer's Tavern, Dungeon Delve, quiz, dice, searchable Codex | Six PHP pages and three assets HTTP 200, PHP lint passed |
| V4 | `/hollowdeep-preview-v4/` | Daily Chronicle, Rune Memory, Tavern Passport stamps, mobile quick navigation | Ten HTTP 200 responses, PHP lint passed; **seven browser functional tests passed, zero failed** |
| V5 | `/hollowdeep-preview-v5/` | Adventure Hub, activity links, summary of locally saved stamps/plans, surprise activity | Eleven HTTP 200 responses, PHP lint passed; **V5 client-side functional tests pending** |

The V4 browser test page was deployed separately at `/hollowdeep-preview-v4-qa/index.html`. The owner supplied a screenshot showing 7 passed and 0 failed. HTTP 200 is a delivery check, not proof of JavaScript behavior.

## V5 entry points

- Homepage: `/hollowdeep-preview-v5/index.php`
- Adventure Hub: `/hollowdeep-preview-v5/hub.php`
- Tavern: `/hollowdeep-preview-v5/tavern.php`
- Codex: `/hollowdeep-preview-v5/codex.php`
- Daily Challenge: `/hollowdeep-preview-v5/daily.php`
- Player Portal: `/hollowdeep-preview-v5/portal.php`

The local quest planner uses browser localStorage. The Tavern Passport and Daily Chronicle also store activity locally in the browser. **None are real Mordor character data, XP, gold, achievements, or game-server rewards.**

## Deployment boundaries

- The host's PHP previews reside under `/var/www/hollowdeep/public/` in versioned directories. Do not confuse them with the native C engine or the repository's separate web application.
- Previous previews, existing production homepage, administration tools, database, and native game server were reported unchanged by the installation checks.
- These website deployments were not confirmed as the live homepage.
- Browser play needs a separately authenticated TLS WebSocket-to-Telnet bridge; do not represent a static Play page as a live connected client.
- Never publish player saves, private server configuration, database credentials, signing keys, passwords, or production logs.

## Validation before considering promotion

1. Run `php -l` on every PHP file and verify that pages, scripts, and stylesheets respond successfully.
2. Use the real browser to check the V5 Adventure Hub counts, the Daily status, activity navigation, and mobile layout. The host did not have Node.js installed during these previews.
3. Exercise keyboard and touch navigation and make sure buttons do not navigate unexpectedly.
4. Ensure that activities do not claim to change the game character or server.
5. Compare source checksums of the old preview before and after installing the new one.
6. Promote to the primary site only with deliberate rollback planning and a separate deployment approval. Do not overwrite the current admin dashboard.

## Work remaining

- Verify V5 JavaScript in a browser and complete a mobile UX review.
- Organize and publish the PHP source files separately from this guide if they are exported from the server and reviewed for secrets. The code snippets used to install previews are not automatically synchronized to this GitHub repository.
- Prepare a Discord changelog/announcement once the next release is validated. A local changelog file does not itself publish to Discord.
- Keep V22 combat-target work on hold until the website milestone is finished.
