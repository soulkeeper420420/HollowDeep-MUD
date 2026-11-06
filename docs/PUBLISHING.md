# Publishing Hollowdeep

The public repository is [soulkeeper420420/HollowDeep-MUD](https://github.com/soulkeeper420420/HollowDeep-MUD). Publish completed, tested changes with matching help and guides. A GitHub commit, a website deployment and a live native update are three separate outcomes; report each accurately.

## Before publishing source

1. Update relevant in-game help and the player, staff or server guide. Update the [Atlas comparison](ATLAS_COMPARISON.md) when feature coverage changes.
2. Run client/bridge tests and the TypeScript check. Build and test native changes, including the disposable multiplayer smoke test on a host with local TCP sockets.
3. Refresh the downloadable kit and source manifest when engine or bridge files change:

   ```sh
   node scripts/package-server-kit.mjs /path/to/Mordor_3.00.tar.gz
   ```

4. Review the resulting kit SHA-256 and update the expected kit digest in `deploy/install-ubuntu.sh`, `deploy/enable-public.py`, `deploy/console-bootstrap.py` and `deploy/make-console-setup.py` together. Their pins intentionally reject an unreviewed replacement. Do not change the separate legacy baseline pins to match a new kit.
5. Generate and test the console setup, native updater and browser installer. Copy the reviewed native updater and browser installer from `outputs/` into `deploy/artifacts/`, then refresh `deploy/artifacts/SHA256SUMS` from those exact two files. These tracked artifacts let mobile host operators download the release without building it. Exclude credentials, player files, private backups and host logs from publication.
6. Commit the complete source state and push it to `main`, or use a pull request for review. The GitHub verification workflow runs on pushes and pull requests and retains installer artifacts after successful checks. A queued workflow is not a passed check.

The workflow tests on Ubuntu 24.04 with multilib GCC, Python 3.12 and Node 22. It builds the original engine as ELF32 and starts disposable local test worlds. It has read-only repository permissions and does not restart the live Linode or publish the website.

## Generate installation artifacts

From the repository root:

```sh
python3 deploy/make-console-setup.py
python3 deploy/make-native-update.py
python3 deploy/make-bridge-installer.py
```

- `outputs/hollowdeep-native-update.py` updates the known working installation after checking its baseline and preserving its world and saves. Its pinned baseline is bundled under `deploy/baseline/`; generating it does not require the original private Git history.
- `outputs/hollowdeep-browser-setup.py` installs the separate bridge and TLS services, carrying only the public verification key.
- `outputs/hollowdeep-console-setup.html` and `.txt` are for a **fresh host**, not an update over the working world.

Reviewed copies of the native and browser installers are also published in [`deploy/artifacts/`](../deploy/artifacts/) with `SHA256SUMS`. Their contents must match the generated source at the published commit.

The older `make-runtime-recovery.py` uses the pinned legacy kit and recovered test from `deploy/baseline/`. CI verifies it separately. It repairs the earlier installation failure; use the native feature updater for the already working server.

## Publish the website

Use the existing Sites project recorded in `.openai/hosting.json`. Build the source, push that exact commit to the project's configured source remote, save a version from that commit and its matching build artifact, then deploy the saved version. Preserve the existing public audience. Check the resulting deployment status and production URL.

The GitHub repository and Sites source remote are separate. A successful GitHub push does not prove the Sites remote was updated. If source push or deployment access is unavailable, keep the build and report the blocked step instead of marking the site as published.

Runtime signing keys belong in Sites settings. A new version must use configuration matching the bridge's public key; do not put private keys in the hosting manifest or a deployment archive.

## Update the running server

Follow the [server guide](SERVER_GUIDE.md), using a planned empty-server window for a native update. The website and bridge can be published independently of the native engine, but new native commands require the replacement engine to be active.

After installation, verify a real native login, progression/help commands, staff restrictions, save/logout and reconnect. After the bridge is installed, verify trusted HTTPS and a full browser sign-in and character session. Retain the updater's backup and final result privately.

A release note should identify the source commit, checks that actually passed, website version/deployment result, and whether the Linode update and browser session were verified. Pending deployment steps should remain explicit.
