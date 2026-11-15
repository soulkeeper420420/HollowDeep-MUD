# Round 73 foundation validation

## Local tests (not native gameplay)

- Python 3.13.5: `python3 -m unittest -v test_treasure`
- Seven unit tests: **PASS**.
- Covers deterministic treasure blueprint metadata, invalid site rejection, early claim denial, distinct verified kills, duplicate event rejection, a persistent exact reward snapshot, 20 concurrent claim retries, restart/recovery and receipt idempotency.
- Tests are source-level demonstrations of the intended state transitions. There is no engine combat/pickup integration here, and the presence of valid metadata does not create a locked chest in native gameplay.

## Linode private regression gate

**Pending user execution** until the one-pass isolated continuation script runs successfully on the authorized Linode host. The script checks the production service and fixture hashes before/after, recompiles the private native engine and repeats Round 59–72 native/browser regressions plus these Round 73 unit tests. Private logs remain outside GitHub.

## Round 73B map possession / locate foundation

- Added immutable map-specific clues stored with each activated encounter.
- Added a `locate` rule API that requires matching map **instance** ID in a
  trusted live inventory snapshot; no coordinates are revealed from the API.
- Chest claims now fail closed when the map is absent, swapped, lost or
  omitted from the trusted inventory snapshot, even after guardian defeats.
- Multiple carried maps require explicit selection; ownership remains bound.
- Local Python 3.13: **11 of 11** unit tests passed, including earlier
  idempotent claims, concurrent requests and crash/reopen tests.
- Private Linode full regression suite for these changes: **PENDING** until
  the one-pass runner is executed. This is **not yet a native `locate` command**.

## Round 73B full private Linode validation

- Tested base commit: `538922a084f31a05a22675b4037850a98e8d7133`, with four reviewed Round 73B files applied.
- Python 11/11 map-possession/claim tests and Round 59–72 browser/native suite: **PASS**.
- Production and prior fixture hashes/service identity: **UNCHANGED**.
- Private regression log SHA-256: `fabbc1fe2b7bc6617071f2ee499900101bea6eaa69dec992bb0479aad933ee31` (log not published).
- Native C `locate`, real map pickup, guardian/chest interception and durable
  item delivery: **NOT IMPLEMENTED / NOT TESTED**.

## Round 73C — read-only native locate candidate (private Linode replay)

- Tested Round 73B parent source: `355fda16ce2ea52d629cd3fd2840b6a78ff5b3e2`, plus exactly six reviewed Round 73C source/docs file changes.
- Native C 32-bit build, actual in-game pickup/locate/drop/owner-isolation, Round 59–72 browser and native suite, Round 73B 11 tests: **PASS**.
- Protected production/fixture hashes and running service identity: **UNCHANGED**.
- Private regression SHA-256: `979a0ca4f0b325fb603d5daeec489e9c4c949a456ebbac67a76f033862ad3b4a`. Private log not committed.
- This validates only a read-only clue command with a trusted fixture sidecar;
  unique map minting, guardian combat, chest pickup locks, enchanted item
  delivery and crash-safe native receipts: **NOT IMPLEMENTED OR ENABLED**.


## Round 73D — virtual chest isolated native gameplay

- Offline C harness: exact guardian pointer matching, actual-owner death,
  wrong-owner death, duplicate-open denial, lost-map denial and malformed
  sidecar rejection: **PASS before Linode native replay**.
- Linode 32-bit native combat and full browser/native regression: **PENDING**.
- No native treasure loot; no production deployment or service restart.

## Round 73D isolated Linode gameplay validation

- Tested Round 73C source: 3fedae0d781e1e49a7cd5ab9702558b1ba969ae2, plus exactly eight reviewed paths.
- Offline C security harness and native 32-bit build: PASS.
- Actual native guardian defeat, chest lock/unlock, physical map requirement,
  and repeated-open without treasure rewards: PASS.
- Full Round 59-73C native/browser regressions: PASS.
- Production source, rooms, fixtures, executable/service identity: UNCHANGED.
- Private regression log SHA-256: cad995924f4f64b8c2315fbc08e6d6531e3203f9b9c472a649278557cf8a2dbc (log not published).
- Real loot, respawn reset, party sharing, durable item claim receipts and
  live deployment: NOT IMPLEMENTED.
