# HollowDeep MUD — Round 79AC1: native three-receipt dismount commands

Accepted private ELF32 milestone on 2026-11-22: native atomic dismount,
full native MUD build, mock failure regressions, and isolated socket PASS.
No production deployment, player-save/world modification, service restart,
or mount award/boarding/stabling/retrieval.

This milestone upgrades the player command adapter from the legacy two-receipt
read/dismount path to the accepted Round79AB three-receipt store. `mount list`
and `mount status` require a consistent physical presence receipt (80/81/82).
`dismount` checks a native player room and atomically commits all three under
the existing player-file lock. Failure, CAS conflict and uncertain-rename
results fail closed unless the exact new 80/81/82 state is recovered.

`mount ID`, `stable ID`, `retrieve ID` continue to deny without real native
mount-entity ownership/presence. Mounted wilderness movement is not wired.

The Linode runner executes private staging tests, mock native command tests,
mock transaction failure tests, a full synthetic native player-file ELF32
replay, an entire feature-gated ELF32 MUD rebuild, and a real isolated socket
replay of the existing stablecheck/Breath/listing regression. All tests run
in disposable `/tmp` and `/root/hollowdeep-dev/round79ac-*` directories.

The correct accepted source input is the **Round79AB R2 private ELF32 source**
from `/root/hollowdeep-dev/round79ab-oPXa64jA/run.log`. The pinned public
Round79Z socket fixture is reused without touching source fixture data.
