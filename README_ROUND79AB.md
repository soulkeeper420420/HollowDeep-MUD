# Round 79AB — Private three-receipt mount location save

Native candidate for HollowDeep MUD. Pure tests locally; private ELF32
atomic player-file tests on Linode required. No production deployment.

The feature-gated patch disables the old two-receipt writer and requires
all three mount receipts to be consistent with the authoritative Breath
character epoch and CAS revision. No gameplay boarding/travel is enabled.

Use `tools/gameplay/round79/private_mount_presence_store_round79ab.sh`
with a new private result directory and the accepted Round79Z private source.
