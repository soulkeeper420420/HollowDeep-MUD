# Hollowdeep server guide

Source repository: [soulkeeper420420/HollowDeep-MUD](https://github.com/soulkeeper420420/HollowDeep-MUD).

## Deployment status

The host confirmed native mobile-client access to **172.233.176.81:4040**. That confirms the earlier native installation, not installation of every later source change.

This source update adds combat stances, staff roles/moderation and compact progression guides. Apply the native updater to install them on the existing world. Browser play requires the separate browser bridge installer and matching Sites runtime configuration. Neither publishing source nor publishing the website restarts or changes the Linode automatically.

The target is Ubuntu 24.04 LTS on x86_64. The native engine requires Python 3, Make and a working **32-bit-capable GCC toolchain** (`build-essential`, `gcc-multilib`, `libc6-dev-i386`). Original Mordor world files serialize native structures; a 64-bit engine is incompatible with them.

## Access from a phone

Use a mobile SFTP app to upload supplied deployment files, or use a terminal with SSH/SFTP support. The host is `172.233.176.81`, SSH/SFTP port is normally `22`, and the configured administration login is `root`. Enter the Linux password or SSH key in that app, not in the game or repository.

Linode's browser-based Lish/Weblish console provides the Linux command prompt without a Telnet connection to the game. Inside that console, `telnet 127.0.0.1 4040` reaches the local game. A mobile MUD app connects to the public IP and port 4040 instead.

## Download the reviewed installers from Lish

On a phone, the simplest path is to paste these commands into the signed-in **root Lish console**. They download the published scripts and verify their SHA-256 values before you run either installer:

```sh
mkdir -p /root/hollowdeep-downloads
cd /root/hollowdeep-downloads
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-native-update.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/hollowdeep-browser-setup.py
curl -fSLO https://raw.githubusercontent.com/soulkeeper420420/HollowDeep-MUD/main/deploy/artifacts/SHA256SUMS
sha256sum --check SHA256SUMS
```

Continue only when both files report `OK`. If a download or checksum fails, keep the error output and resolve it before running the scripts. You can also upload the same files with SFTP to the directory above.

## Update the working native game

Use the generated `hollowdeep-native-update.py` artifact supplied for this installation. **Do not rerun the fresh installer over the working world.**

1. Tell players to use `save`, then `quit`; wait for any quit cooldown and retry `quit` if needed.
2. Download and verify the scripts as above, or upload the reviewed updater to `/root/hollowdeep-downloads/hollowdeep-native-update.py`.
3. In Lish, run:

   ```sh
   python3 /root/hollowdeep-downloads/hollowdeep-native-update.py
   ```

The updater checks the expected installation, original file hashes, service settings and player connections. It builds and tests a separate candidate, retains a private backup, and checks the replacement locally before restoring the existing public binding. It retains player, room, object and Chronicle data. Changed local source or unexpected service overrides require review; do not remove guards to force an update.

After success, reconnect and verify:

```text
hprofile status
hclass progress
hquest next
hstance
hstaff whoami
```

Use a normal playable character to test stance effects. Realmkeeper has administrative-class behavior. Record the updater's final output and the printed backup location.

The updater generator is `python3 deploy/make-native-update.py`. It uses the checksum-pinned legacy kit and manifest under `deploy/baseline/`, so a fresh repository clone can generate it without the original Git history. The older runtime-recovery generator remains a separate historical tool.

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
