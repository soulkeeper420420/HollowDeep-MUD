# Hollowdeep on your Ubuntu 24.04 Linode

Target: `172.233.176.81`, Ubuntu 24.04 LTS, x86_64. Default native MUD port: **4040**.

**Already running Hollowdeep?** Use the [server update guide](../docs/SERVER_GUIDE.md) and the native updater. The fresh installer below refuses to overwrite an existing game. Browser connection setup is a separate installer and preserves the native service.

This bundle includes the corrected original Mordor server kit. It does not use the older kit currently published on the website. No server changes happen until you run the installer on your Linode. The installer requires root and refuses to replace an existing Hollowdeep directory, service, or account.

## Console setup without uploading a file

If you received `hollowdeep-console-setup.html`, open it, click **Copy complete installer**, and paste the complete block into the root Lish console on `172.233.176.81`. The matching `.txt` file contains the same block. This verifies the target and source, builds the corrected kit, and runs the installer below automatically. Skip sections 1 and 2.

After it finishes, create your administrator using section 3. For this console workflow, the public activation command in section 4 is:

```sh
python3 /root/hollowdeep-console/enable-public.py
```

Keep the console output if anything fails. The setup preserves existing installations and does not retry over a partially created world.

## 1. Upload this bundle

Download `hollowdeep-linode.tar.gz` from the chat. From a terminal on the computer where you downloaded it, upload it with:

```sh
scp hollowdeep-linode.tar.gz root@172.233.176.81:/root/
```

This uses SSH port 22. Enter your Linode's Linux root password or use your configured SSH key; your Cloud Manager login is a separate account. If SSH is disabled, use your usual SFTP client or arrange SSH access through the Linode console. The Lish console itself does not upload local files.

## 2. Install from the Linode console

In Lish or an SSH session on the Linode, run:

```sh
cd /root
tar -xzf hollowdeep-linode.tar.gz
cd hollowdeep-linode
bash install-ubuntu.sh ./hollowdeep-server-kit.tar.gz
```

The installer verifies the kit checksum, installs the 32-bit compiler prerequisites, creates an unprivileged `hollowdeep` service account, builds the engine, and runs the actual two-player runtime smoke test. Only after all tests pass does it start `hollowdeep.service`, initially on **127.0.0.1:4040**. It does not stop other services, reboot the machine, or enable a firewall.

If a test fails, the script stops before public startup. Keep its output and share the error so we can fix it. Do not remove the 32-bit compiler flags or delete an existing world to force the installer through.

## 3. Create your administrator locally

Still on the Linode, run:

```sh
telnet 127.0.0.1 4040
```

Create the character **Realmkeeper**, the administrative name configured by this installer. Follow the original game's prompts. For a straightforward initial character, choose fighter, stats `14 10 12 10 8`, sharp weapon, lawful, and human. Choose your own password when prompted; it stays inside the game session. The original engine allows 3–14 characters. The configured administrative name is promoted by the original engine when initialized.

Once in the game, type:

```text
save
quit
```

## 4. Open the game to MUD clients

Ensure the administrator has quit and no local test clients remain connected, then run:

```sh
cd /root/hollowdeep-linode
python3 enable-public.py
```

This checks that the administrator save exists, refuses a restart while clients are connected, switches the service to public IPv4 binding, and verifies the original login greeting. If UFW is already active it adds only the selected game TCP port; it never enables UFW or changes SSH rules. Other firewall managers must be configured separately.

In Cloud Manager, check whether a **Cloud Firewall** is attached to this Linode. If one is attached, add an inbound **TCP / 4040 / Allow** rule for the players who should have access (for a public game, IPv4 source `0.0.0.0/0`) and save it. Preserve the existing SSH and other rules.

Then connect from Mudlet, MUSHclient, or another MUD client:

| Setting | Value |
| --- | --- |
| Host | `172.233.176.81` |
| Port | `4040` |
| Protocol | Telnet |
| SSL/TLS | Off |

The first external connection confirms that the Linode firewall and host firewall both permit the game. Native Telnet is unencrypted; use a password unique to this game.

## Operation and further changes

```sh
systemctl status hollowdeep.service --no-pager
journalctl -u hollowdeep.service -n 60 --no-pager
```

Source is under `/srv/hollowdeep/world/src_3.00`. Persistent data is under `/srv/hollowdeep/world`, including `player/`, `hollowdeep-data/`, rooms, and objects. Back it up before changing the installation. Have players save and quit before restarting; the original engine does not guarantee a save on SIGTERM.

For browser play, use the separate browser setup described in the [server guide](../docs/SERVER_GUIDE.md). It installs Node, the bridge, and Caddy TLS with a public verification key. The private signing key stays in Sites. This fresh native installer does not configure browser TLS.

Verification before delivery: original 32-bit engine compilation/linking and socket-free input tests passed in the build workspace; this deployment script has not been run on your Linode. Its runtime smoke test is the required host verification step.
