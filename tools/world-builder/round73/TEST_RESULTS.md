# Round 73 foundation validation

## Local tests (not native gameplay)

- Python 3.13.5: `python3 -m unittest -v test_treasure`
- Seven unit tests: **PASS**.
- Covers deterministic treasure blueprint metadata, invalid site rejection, early claim denial, distinct verified kills, duplicate event rejection, a persistent exact reward snapshot, 20 concurrent claim retries, restart/recovery and receipt idempotency.
- Tests are source-level demonstrations of the intended state transitions. There is no engine combat/pickup integration here, and the presence of valid metadata does not create a locked chest in native gameplay.

## Linode private regression gate

**Pending user execution** until the one-pass isolated continuation script runs successfully on the authorized Linode host. The script checks the production service and fixture hashes before/after, recompiles the private native engine and repeats Round 59–72 native/browser regressions plus these Round 73 unit tests. Private logs remain outside GitHub.

## Complete Linode regression (script execution)

- Source base: `34f3b95fc51afd701ece16b514409c1ba8d56d32`
- Round 59–72 private browser/native suite plus Round 73 blueprint/ledger tests: **PASS**.
- Production and prior fixture: **UNCHANGED**; no service restart.
- Private regression log SHA-256 (log is not published): `b1b172d5978e52e99bfa491f4457e925f889c79aeac028b36d102dc228a5b3fd`
- Native guardian pickup-lock, map-item and inventory-save integration: **NOT YET IMPLEMENTED OR CLAIMED**.
