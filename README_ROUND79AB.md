# Round 79AB — Private three-receipt mount location save

Accepted private ELF32 test milestone on Linode, 2026-11-22.
Native atomic player-file, regression, full game ELF32 compile: PASS.
No production deployment.

The feature-gated patch disables the old two-receipt writer and requires
all three mount receipts to be consistent with the authoritative Breath
character epoch and CAS revision. No gameplay boarding/travel is enabled.

Use `tools/gameplay/round79/private_mount_presence_store_round79ab.sh`
with a new private result directory and the accepted Round79Z private source.
