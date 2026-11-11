# Round 11Q deployment decision

**NO-GO for production deployment. GO for review of the isolated security and rollback results.** The candidate passed the requested isolated checks. The rehearsal still uses private copies of rooms 1 and 2 as the guild district entry and stockroom. A production release needs a verified connection from the live world into the guild district and an exact manifest for that connection. A controlled rollout also needs an explicit decision about preserving or reconciling guild transactions made after activation if the predecessor is restored.

## Verified results

The private Linode replay passed **23/23** assertions using the SHA-256-pinned Round 11P candidate, `12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c`. Three assertions created and saved disposable characters. Eighteen exercised movement. Two checked rollback data and predecessor login.

| Native entry route | Hall A (6003) | Hall B (6006) | Hall C (6009) |
| --- | --- | --- | --- |
| Cast teleport on self | Outsider denied, moderator admitted | Outsider denied, moderator admitted | Outsider denied, moderator admitted |
| Pit trap movement | Outsider denied, moderator admitted | Outsider denied, moderator admitted | Outsider denied, moderator admitted |
| Native staff teleport | Caretaker without guild or sidecar role denied, moderator admitted | Caretaker without guild or sidecar role denied, moderator admitted | Caretaker without guild or sidecar role denied, moderator admitted |

The unmodified candidate executed the native commands. An offline helper gave disposable characters the spell and native caretaker class. A private RNG library selected deterministic teleport destinations and pit trap rolls. The trap room headers and staff role records were edited only inside the rehearsal. Admitted cases exercised moderator access. Ordinary member access and role fallback were covered by the prior populated replay.

## Complete isolated rollback

The launcher copied the current production source and room trees into a private predecessor snapshot. It applied the candidate source delta, binary and private guild rooms in a separate runtime tree. After gameplay, it restored the full source and room trees and the exact predecessor binary, SHA-256 `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5`. The restored files matched by checksum. Path types, modes and numeric ownership matched the predecessor snapshot. Saved state bytes matched before and after the rollback, and a character saved by the candidate logged in on the exact predecessor and ran `score`.

The rollback used disposable character saves and no populated guild ledger. The Round 11P predecessor boot separately preserved a populated ledger and three saves byte for byte. The rehearsal does not establish how an operator should handle new guild transactions during a live rollback.

Production source, production rooms, live service identity and both earlier private stages matched their before/after checks. No deployment or live restart occurred.

Run the rehearsal on the authorized private Linode host with `bash round11q_private.sh`. Keep the Python runner and both C fixtures next to the launcher. The launcher pins both binaries and runs the game in private mount, network and PID namespaces.
