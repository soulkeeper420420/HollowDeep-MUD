# Round 11O native character writer faults

Verified on November 10, 2026. The native replay passed all 84 assertions. The production source and Round 11K private stage checksums matched before and after the run.

Run `bash round11n_private_replay.sh --native-writer-faults` on the private test host with `round11n_patch.py` and `round11o_writer_faults.py` next to the launcher. The default invocation still runs the Round 11N transaction-boundary replay.

Round 11E exercised faults in the extracted atomic character writer. Round 11O uses the native game, guild command, compressed character serializer, and atomic writer together in a fresh isolated stage.

- Limit each write to seven bytes while the first founder's guild transaction saves the character. Reload the founding save after a native restart and verify that it contains exactly one blade that can be wielded.
- Simulate an `EIO` return at the character file's pre-rename `fsync` boundary after the second founder's guild ledger commits. Verify the old primary byte for byte and check that the temporary file was removed. Restart using the old save and verify that the committed guild survives and the spent deed is reconciled.

These checks cover the native character writer. The ledger failure still uses the Round 11N caller hook. Native-process termination, directory sync failures, and faults inside the ledger writer remain open.
