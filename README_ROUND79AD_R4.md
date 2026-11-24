# Round79AD R4 — Private pre-remove death bridge (NOT gameplay release)

R3 confirmed native `80/81/82/83` atomic save and failure/replay PASS.
R4 connects an **unexposed** private `del_crt_rom` death precheck to the
registered exact native mount pointer and owner, then saves the monotone
#83 tombstone through R3's four-receipt locked CAS. On an uncertain rename it
checks the exact new four-receipt state before acknowledging. The live player
and world source remain unmodified; feature is enabled only in a disposable
ELF32 game build.

Test only with
`tools/gameplay/round79/private_mount_ad_combat_death.sh WORK SOURCE`,
where `WORK` is new `/root/hollowdeep-dev/round79ad-*` and `SOURCE` is
`/tmp/hd-army-game-round79adfour-03lRN95P/src`.

The nine local staging regressions and private simulated death-save C tests
passed. **Native Linode ELF32 and socket replay pending.** Even if they pass,
full combat-death coverage, safe login restore, authenticated player actions,
reversible entity side effects and atomic mounted travel are not implemented
or authorized. No production deployment, game award, public command, or
Discord release announcement.
