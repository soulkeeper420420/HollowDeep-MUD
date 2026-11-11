# Round 11N private guild save replay

Verified on the private test host on November 10, 2026. All 84 assertions passed, including the 73 Round 11K assertions. The production source and previous private stage checksums matched before and after the replay. The native server ran in the disposable network, PID, and mount namespaces.

Run `bash round11n_private_replay.sh` with both Round 11N scripts in the same directory on the authorized private test host. The launcher requires the passing Round 11K result and checks the production source and prior private stage before and after the replay. It creates a fresh chroot with empty player and ledger directories. Keep the build and gameplay logs in that private stage.

The replay extends the 73 Round 11K assertions with 11 checks. A disposable test character grants a native weapon through the compile-time isolated funds command, wields it through the ordinary player command, and founds a guild. After the native server stops, the runner restores the exact character bytes captured immediately after founding. The restarted server must load exactly one blade into inventory and allow the player to wield it again.

The first founding attempt injects a failure before the ledger write. The runner checks that the ledger is unchanged and the deed remains usable. A second founder exercises a character-save failure after the ledger commits. The runner restores the stale character save at restart and verifies that the guild remains registered and the spent deed is reconciled. The fault hooks simulate a failed operation at each transaction boundary. They do not exercise partial writes, fsync failures, or abrupt termination within either writer.
