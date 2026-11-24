# Round79AD R6B: unaccepted private atomic mount action writer

Candidate-only source. From the verified R6A private source, run
`tools/gameplay/round79/private_mount_ad_four_action.sh` in an isolated Linode
work root to verify real ELF32 board/dismount transactions, fault injection,
and six native mount deaths. No production deployment, no command exposure.

All private sources live under `tools/gameplay/round79/`; see
`docs/ROUND79AD_R6B_PRIVATE_ACTION_CAS.md` for exact invariants, staged edits,
remaining safety gaps, and validation gates.
