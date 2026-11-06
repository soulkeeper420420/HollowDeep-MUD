# HollowDeep server guide

Source: [soulkeeper420420/HollowDeep-MUD](https://github.com/soulkeeper420420/HollowDeep-MUD).

## Current status and the correct updater

The host confirmed native access at **172.233.176.81:4040** and completion of the earlier spells update. The later builder update failed in its disposable test on a long room-name command; it did not activate. The new release repairs that parser overflow and adds builder/DM powers, Implementor roles, bonus tiers, full help indexing, skills, staff labels and the staff-only clan. **Publication is not confirmation of live installation.**

Use Ubuntu 24.04 x86_64 with Python 3, Make and 32-bit GCC support. Do not rerun a fresh installer over the world, delete installation records, remove checks, or remove `-m32`.

In the Linode root Lish console, read the completed update record:

```sh
cat /etc/hollowdeep/native-update.json
```

Match its payload hash to this table. A failed candidate does not replace the completed record.

| Completed predecessor payload | Artifact for this release |
| --- | --- |
| `6b7331917578a7963453245ee2b64d5e3ab929cddbe64635aa5008fb46f734ee` (spells; last confirmed) | `hollowdeep-native-update.py` |
| `5017286c11aeaba8b539a8c9be841c815db56f63561bf4ff976838657da7dccb` (staff/builder parser repair, if you subsequently installed it) | `hollowdeep-native-update-from-repair.py` |
| No native update record, and the exact pinned original pre-feature installation | `hollowdeep-native-update-from-legacy.py` — requires that baseline; not for the confirmed spells server. |
| Any other hash, missing/unexpected metadata, or local source edits | Keep the world intact and review the record/output before choosing a migration. |

These alternatives are **not a sequence**. Run only the artifact for the completed predecessor. Each verifies its own baseline and refuses mismatches.

## Download and install from Lish

The release carries all artifacts and their hashes in [deploy/artifacts](../deploy/artifacts/). Downloading does not run them:

```sh
mkdir -p /root/hollowdeep-downloads
cd /root/hollowdeep-downloads
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-native-update.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-native-update-from-repair.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-native-update-from-legacy.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-browser-setup.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/SHA256SUMS
sha256sum --check SHA256SUMS
```

Continue only when the downloads succeed and every checksum reports `OK`. For a durable release pin, replace `main` in all five URLs with the same reviewed commit SHA. SFTP/WinSCP upload of those exact files is an alternative; SSH/SFTP uses port 22, not the game's port 4040.

Have everyone use `save`, then `quit` and wait/retry if the game requests a cooldown. For the **last confirmed spells installation**, run:

```sh
python3 /root/hollowdeep-downloads/hollowdeep-native-update.py
```

If the record instead matches the repair row, run its `-from-repair.py` file. The updater validates the expected host, service settings, source/binary hashes and disconnected players; builds and tests a separate world; rechecks the installation; and only then backs up and activates. It retains player, room, object, Chronicle, stance and staff data and existing service access settings. Keep the private backup path and final output. A candidate failure before activation leaves the running installation unchanged.

After `Native update installed and login verified`, reconnect and check:

```text
help commands
help search staff
skills
skills all
spells
dmcommands
hstaff whoami
staffclan
hbuild mine
hbonus
```

Test staff-only commands with a staff character and denied access with a normal player. Check role badges using `who`. Save/logout and reconnect. The [staff](STAFF_GUIDE.md), [building](BUILDING_GUIDE.md) and [player](PLAYER_GUIDE.md) guides describe the exact permissions.

The earlier `hollowdeep-builder-events-update.py` is superseded because of its parser failure. `hollowdeep-staff-builder-repair.py` is a completed predecessor source, not the newest feature package. Historical runtime recovery remains separate. Proposed XP curves, remorts, new classes/spells and quest areas are not installed by this release.

## Generate matching packages from source

The release includes checksum-pinned historical updaters under `deploy/baseline/` for reproducible successor generation. Their embedded data is public source, not player saves. Do not run these historical copies as new installers.

```sh
python3 deploy/make-native-update.py --from-update deploy/baseline/spells-update.py --from-sha256 2e366aac5195273541d4d1ad033e3352eb14eab484b0bcf0564bca7932bcfe81
```

The output is `outputs/hollowdeep-native-update.py`. To target the repair baseline, substitute `deploy/baseline/staff-builder-repair.py` and SHA `3f1bdb212d5fc7c95c6967c0be93dc280b816f11654e30151f8d085571ac4316`. With neither option the generator targets the historical legacy baseline; its default output filename alone does not identify compatibility. Inspect the manifest or exact generation command.

The generator parses literal constants and verifies hashes instead of executing the supplied predecessor. It reproduces kit/world manifests, rejects serialized-structure changes and removed files, and includes the new help/permission tests in pre-activation checks.

## Connect the website

The native game and website transport are separate services. The generated `hollowdeep-browser-setup.py` installs an authenticated Node.js bridge and Caddy TLS endpoint without changing `hollowdeep.service`.

1. Ensure an attached Linode Cloud Firewall permits inbound TCP **80 and 443** for certificate issuance and browser traffic. Keep TCP **4040** available for native players.
2. Download and verify the scripts as above, or upload the reviewed bridge installer to `/root/hollowdeep-downloads/hollowdeep-browser-setup.py`.
3. Run:

   ```sh
   python3 /root/hollowdeep-downloads/hollowdeep-browser-setup.py
   ```

The installer uses checksum-pinned dependencies, a public verification key and automatic certificate renewal. If HTTPS is not yet verified, read the reported TLS logs and firewall instructions. Do not treat a service installation message alone as proof that browser play works.

Check the endpoint from the Linode:

```sh
curl --fail https://172.233.176.81/health
```

For this deployment, the browser endpoint is `wss://172.233.176.81/socket`. Configure these values in **Sites runtime settings**, then deploy the matching website version:

| Variable | Where it belongs | Purpose |
| --- | --- | --- |
| `BRIDGE_URL` | Sites | `wss://172.233.176.81/socket` |
| `BRIDGE_SIGNING_KEY_PKCS8` | Sites secret only | Base64 DER Ed25519 private signing key. |
| `MUD_PUBLIC_HOST` | Sites | `172.233.176.81` |
| `MUD_PUBLIC_PORT` | Sites | `4040` |
| `BRIDGE_PUBLIC_KEY_SPKI` | Bridge | Matching base64 DER Ed25519 public verification key. |
| `ALLOWED_ORIGINS` | Bridge | `https://hollowdeep-dungeon.soulkeeper420.chatgpt.site` |

The bridge installer carries only the public key. Keep private signing keys out of Git, downloaded source, frontend code and the hosting manifest. The earlier shared-secret mode is retained for compatibility; a new installation should use the matching signing/public-key pair.

After trusted HTTPS and matching runtime configuration are confirmed, open the [website](https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/), sign in with ChatGPT, connect, and log in to a Mordor character. Test a complete login and logout, not only `/health`.

## Service checks

These commands inspect the host without restarting the game:

```sh
systemctl status hollowdeep.service --no-pager -l
ss -ltnp 'sport = :4040'
journalctl -u hollowdeep.service -n 40 --no-pager
systemctl status hollowdeep-web.service hollowdeep-web-tls.service --no-pager -l
journalctl -u hollowdeep-web-tls.service -n 40 --no-pager
```

The native service is `hollowdeep.service`; browser services are `hollowdeep-web.service` and `hollowdeep-web-tls.service`. Save and quit all players before a manual native restart. Preserve the TLS service's data directory so certificate renewals retain their state.

## Data and source locations

| Location | Contents |
| --- | --- |
| `/srv/hollowdeep/world/src_3.00/` | Prepared native C source and compiled engine. |
| `/srv/hollowdeep/world/player/` | Original player account saves. |
| `/srv/hollowdeep/world/rooms/`, `objmon/` | World and object/monster data. |
| `/srv/hollowdeep/world/hollowdeep-data/` | Chronicle journals, stance choices and staff roles/mutes/audit. |
| `/srv/hollowdeep/kit/` | Installed preparation, build and test tools. |
| `/etc/hollowdeep/` | Installation/update records. |

For a consistent manual backup, first have players save and quit, stop the game during a planned maintenance window, then archive the whole world and relevant configuration to a private location. Verify that the backup can be read before modifying source. Never publish player saves, logs containing account information, secrets or TLS private data.

## Edit, test and publish

Use the [server workshop](https://hollowdeep-dungeon.soulkeeper420.chatgpt.site/workshop) for local source drafts and patch export. It does not write to the Linode or restart services. See [the engine guide](../engine/README.md) for compilation and test commands.

Completed changes should include updated in-game help, this documentation, and test results before publication to [GitHub](https://github.com/soulkeeper420420/HollowDeep-MUD). Refresh the downloadable kit and website source manifest, publish the website, and separately apply a verified native/bridge deployment when relevant. A release description should distinguish source publication, website publication and live server installation.
