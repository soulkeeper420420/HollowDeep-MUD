# Hollowdeep

An online multiplayer dungeon using the **original Mordor 3.00 C server**, a browser terminal and native Telnet clients. The game runs on a persistent Linux host; Sites serves the browser interface.

- **Play with a MUD client:** `172.233.176.81`, port `4040`, Telnet.
- **Website:** https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/
- **Source:** https://github.com/soulkeeper420420/HollowDeep-MUD

Native access has been confirmed by the host. The host has confirmed the earlier spells/progression/staff update. New help, skills, builder/event and staff-clan changes in this source version still require their guarded native update to be installed. Browser play needs the separate authenticated TLS bridge and a matching website deployment. Publishing source does not install either service.

## Guides

| Guide | What it covers |
| --- | --- |
| [Player guide](docs/PLAYER_GUIDE.md) | Mobile connection, first commands, combat, progression, Chronicles and groups. |
| [Staff guide](docs/STAFF_GUIDE.md) | Assigning owners, admins and mods; announcements, mutes, kicks and audit records. |
| [Server guide](docs/SERVER_GUIDE.md) | Updating the working Linode, connecting the website, service checks and backups. |
| [Engine development](engine/README.md) | Edit C commands, prepare a world, build ELF32, test and apply workshop patches. |
| [Atlas comparison](docs/ATLAS_COMPARISON.md) | Implemented features and planned work compared with classic The Secret of Atlas. |
| [Command reference](docs/COMMAND_REFERENCE.md) | Every registered command name/alias, with permission notes. |
| [Building](docs/BUILDING_GUIDE.md) | Room allocations, scoped building and DM powers. |
| [Future releases](docs/FUTURE_RELEASES.md) | XP curves, higher levels, remorts, classes, clans and quest-area designs. |
| [Atlas research and quest design](docs/ATLAS_RESEARCH_AND_QUEST_DESIGN.md) | Verified public help observations and original gear/objective-based area proposals. |
| [Release notes](CHANGELOG.md) | Completed source changes and deployment status. |
| [Publishing](docs/PUBLISHING.md) | Checks, generated packages and separate GitHub, website and game deployments. |

## Included

The browser has an ANSI terminal, password masking, command history, a searchable command palette, aliases and manually stepped macros. Its adventure journal and source workshop store local drafts and support export. The [Realm Codex](https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/codex) documents the original classes, spells and commands.

The server retains Mordor's ten playable classes, world, combat and original player-file format. Hollowdeep adds persistent exploration Chronicles with cosmetic badges; compact character and training guidance; balanced, aggressive and guarded combat stances; an owner/admin/mod/implementor hierarchy with moderation and auditing; assigned builder ranges; timed monster-reward events; searchable help; existing skill guidance; and a staff-only clan. In-game help accompanies the added commands. Staff roles do not grant native DM classes or Linux access.

The bridge translates authenticated WebSocket sessions into separate Telnet connections, with origin restrictions, bounded input, ticket replay protection and engine readiness checks. Browser ChatGPT sign-in is separate from the character's Mordor login.

## Develop locally

The website and bridge require Node.js 22.13 or newer. The native engine needs Linux, Python 3, Make and a **32-bit-capable GCC toolchain**. On Ubuntu this normally means `build-essential gcc-multilib libc6-dev-i386`. Do not remove `-m32`: original world data is incompatible with a normal 64-bit build.

```sh
npm ci
npm ci --prefix server
npm run dev
```

The local development client uses `ws://127.0.0.1:8788/socket`; that loopback-only shortcut is excluded from production. Build the website with `npm run build`. The engine guide covers separate native setup and tests.

The browser workshop edits drafts and exports patches. It does not write production files or restart the Linode.

## Hosted browser and bridge configuration

The preferred authentication mode uses Ed25519: only Sites holds the private signing key, and the bridge receives the matching public key. Tickets expire after 60 seconds.

| Setting | Location | Purpose |
| --- | --- | --- |
| `BRIDGE_URL` | Sites | Public `wss://` endpoint ending in `/socket`. |
| `BRIDGE_SIGNING_KEY_PKCS8` | Sites secret | Base64 DER Ed25519 private signing key. |
| `MUD_PUBLIC_HOST`, `MUD_PUBLIC_PORT` | Sites | Native connection details shown to players. |
| `BRIDGE_PUBLIC_KEY_SPKI` | Bridge | Matching base64 DER Ed25519 public verification key. |
| `ALLOWED_ORIGINS` | Bridge | Allowed website origins, separated by commas. |
| `MORDOR_HOST`, `MORDOR_PORT` | Bridge | Native game endpoint; defaults to `127.0.0.1:4040`. |
| `HOST`, `PORT` | Bridge | Listening address and port; the deployment uses `127.0.0.1:8788`. |

Legacy HMAC mode uses a shared `BRIDGE_SECRET` of at least 32 bytes instead of the signing/public-key pair. Configure one authentication mode, not both. Never commit private keys, passwords, player saves or production logs. `MORDOR_ALLOW_LOCAL=1` is only for unsigned loopback development and must remain disabled in public hosting.

Native clients connect directly to the engine using Mordor's character login. Telnet is unencrypted; use a game-specific password.

## Verify

```sh
node --test tests/*.test.mjs server/test/*.test.mjs
node node_modules/typescript/bin/tsc --noEmit
npm run build
```

Bridge integration tests require local TCP sockets. Native tests include behavior checks, 32-bit compilation and a disposable multiplayer world. See [engine/README.md](engine/README.md) and the [verification workflow](.github/workflows/verify.yml). Local socket restrictions can prevent runtime checks in a managed workspace; successful compilation alone does not establish live multiplayer behavior.

## Original engine and notices

Original Mordor 3.00 is by Brett J. Vickers and Brooke Paul. The pinned original distribution is [available here](https://godwars.net/~mudbytes/files/codebases/Mordor_3.00.tar.gz), SHA-256 `05fa24e9d475636bb77020e00a3c2b77a21516af63eef7baf6779ffc1f75e0c0`.

Preserve its included `COPYRIGHT`, `DISCLAIMER` and credits. Do not assume a blanket open-source license grants commercial rights. Hollowdeep does not copy Atlas content or confer rights to Atlas's code, world or assets.
