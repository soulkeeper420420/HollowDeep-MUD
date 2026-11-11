# Round 11P guild candidate manifest

This identifies the exact hook-free private build and its rehearsal assets. Production activation has not been authorized. No deployment package is attached.

| Artifact | SHA-256 |
| --- | --- |
| Candidate `src_3.00/frp.new` | `12111f0dda433201ed3c2139dd92c38db8a0c19f16d2873eda1f56e560b16b4c` |
| Current production predecessor `src_3.00/frp.new` | `b072d152efa769c5f06fcc6f2350387b4d75eec09780687f5b18f5b960143cd5` |
| Production source tree manifest | `0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29` |

## Candidate source delta

The comparison covers top-level C sources, headers, and Makefile against the pinned production source. The social source and header are additions. The other entries replace existing files.

```text
ee3d0c9c3f0d77bebc15d01b7e1a5c9892660632ca9d1c5be89db0af1b4c83d5  Makefile
cf1b4971b95bf96860c5d4d7d1a5a840d50778151f48622bd21ee1490f5854a5  command1.c
7db692304c35728e81e47e12d31cd5c56d1d24403712546b0fcae2864ca7d349  command10.c
a53f460c7f4bb4495b6cfa59190569ae2fcb84528cff7fc137aa57b557dbcd23  command6.c
610e2505406595be9c731f98f7afd7b0d5adec553f276e1df9642131c2f5c8ac  command7.c
445e8911e078ec8b1c6090dfc8e55b68c49c9c587cd5c6b94df19bca6edae403  compress.c
570a34c1c406ac087ce86ce344d3e2a7ebcafb8c54fc66fd33ff1f27eb8eefb8  files2.c
ca450dd3acae56fb642e628f099be1835167833cda9bbe9c1e7cef72b62caca8  global.c
4093b0fe93d4d915ca13e55ec56aa11fd3e84ed4c73fe110702647e0fb9f8ce9  hollowdeep_social.c
f90e67f82f30b431e5cbb7d02816ae4a83abbe629eaa1bed8f0eebc7d8efcbda  hollowdeep_social.h
c4eee2f6c6bb4e6e1dff141aa7b309c4618492e97654869968c88c967802ab53  io.c
c63591027246e55c2a2eeea6cab687e5060f25c0b4b548e5059c1c61776adcec  room.c
```

## Isolated guild rooms

```text
010e13332075ec6efdddce7664df45b58bf6f0a5d0f29b2b80f358f3002c3019  r06000
41d566f4908b1108dc0a4838c8c2ac7dfd188ea913a20da2393bb4cee8be84ee  r06001
3010e631d994f6c59119e70879acaae13776f502b0c8095f841f0862a8258c4b  r06002
2312d495a602e09271772154ebf034e15e203dcd813270b06bdd8a14b4a9107e  r06003
21e7b791f64e6fc41ba4360d9afc6fe5143b87b1589f9dc5499ca778cf8e01cf  r06004
411cb54f58eb644646f9d0456db2729b08bdb5361723df0429f2e16da8f49c5c  r06005
94ffc7ddce13677c29e9a50fb0b2235a67508bafbfb0d0cd29e8dc77f9e6f135  r06006
9fa6f2c4a3566038127987ae646071636c01c587c4edb0074881c8f67dd46b4f  r06007
dc653054f46f52e3462cbadd147ba51ea5cae6d7b0057f1955606120ecf87be1  r06008
f1b830c391e8449f5608b783085832c5463b6e7c967fb40473687dc64bcd0d34  r06009
3dea85877c270c84b998e576eba427b03c74763026aa2054c962f0f2b8a38f2e  r06010
6ee39d20ce9e34082175679ca17cfb7b83ab9d938f4ebbfd3f49e299a0fa9285  r06011
```

The isolated replay replaces rooms 1 and 2 with disposable entry and stock rooms. Those aliases are private test inputs. A production world needs its own entry connection and rollback inventory before the room set can be promoted.

## Verified on Linode

- **90/90 populated replay checks.** A private fixture build established the founding and failure snapshots. The launcher then activated the pinned candidate for recovery and the remaining regression. A saved hall occupant was redirected on login with an invalid guild ledger. An invalid staff database preserved ordinary membership access and denied cross-guild access. A valid moderator role permitted cross-guild access.
- **Exact predecessor rollback.** The replay switched to a checksum-verified private copy of the current production binary. It reached the login prompt with the populated world, and three disposable player saves and the guild ledger remained byte-identical across the predecessor boot.
- **11/11 abrupt recovery checks.** An external 32-bit test library issued SIGKILL just before the ledger rename and, on retry, just before the character rename. The first kill preserved the old primary files and deed. The second left one committed redemption and the old character save. A restart without the test library reconciled the deed and persisted the resulting save while preserving the ledger bytes. The first setup attempt used an invalid-length disposable password and stopped before fault injection. A fresh stage passed all checks.
- Production source and the prior private stage matched their before/after checksums. The live service PID and activation timestamp matched. The tests made no changes to live rooms, saves, services or binaries.

Run the populated replay with `HD_EXACT_CANDIDATE=<candidate> HD_ROLLBACK_BINARY=<private-predecessor-copy> bash round11n_private_replay.sh --exact-candidate`. Run the kill tests with `bash round11p_private_crash.sh <candidate>`. Keep the matching Python and C helpers alongside the launchers.

**Open before release.** Spell teleport, trap movement, and native staff teleport need dynamic access tests. The predecessor rehearsal swapped the binary and checked startup and stored bytes. It did not log in saved characters on the predecessor or rehearse rollback of the full production room and source delta. The two kill checks cover pre-rename process termination and do not establish directory durability under host or power loss.
