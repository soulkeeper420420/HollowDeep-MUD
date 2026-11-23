# HollowDeep Round79AC3D — Read-only monster template audit

A private diagnostic tool, not a gameplay feature. Finds name-based candidates for Horse, Warhorse, Dire Wolf, Nightmare, Griffin and Dark Dragon by reading native template files against a verified ELF32 ABI. It does not select or configure trusted template IDs.

Read-only live monster-template files are permitted; no live game restart, world edits, player reads, catalog activation or generated mount entities. Private output stays on Linode.

Run `tools/gameplay/round79/private_native_template_inventory_round79ac3d.sh` against the accepted AC3C private source.

R3 verified from Linode ABI output: `CMAX=1000`, `MFILESIZE=100`, and a 1,184-byte creature. This candidate scans only the ten native template files the compiled game could index; the read-only native Linode scan **PASS** (exit code 0). Fourteen regression tests passed; eight native template files, 726 living records and 34 unapproved name matches were observed. Candidate IDs/names remain private on Linode.
