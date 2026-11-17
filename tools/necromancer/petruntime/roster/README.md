# Necromancer roster codec

This is the fixed-width roster payload for the private Undead Army work.
The current single-pet store remains the gameplay entry point.

The payload preserves the character epoch and revision and records each
living pet's stable ID, monster template, level, room, HP, MP, XP and stay
flag. Version 2 adds the captured name, unique flag and five base attributes.
Version 1 records still decode with empty names and unset attributes. The allocator's next ID is persisted separately so a later save can
remove a pet without recycling its ID. Records are ordered by increasing
pet ID. The versioned payload uses big-endian integers and has a maximum
size of 1,376 bytes. Decoding requires the exact length and validates the
roster before replacing the caller's state.

Migration reads the existing 64-character single-skeleton receipt. A live
skeleton becomes pet 1 with its saved stats. An empty record or tombstone
becomes an empty roster. Both retain the epoch and revision and reserve
pet 1 permanently. A zero monster template is reserved for this skeleton.

Run from this directory:

```sh
cc -std=gnu89 -Wall -Wextra -Werror hd_pet_roster.c test_pet_roster.c -o /tmp/hd-test-pet-roster
/tmp/hd-test-pet-roster
```

The private native player transaction keeps the roster alongside treasure
receipts, migrates the original receipt on first commit, and preserves
unique identity and stats on ordinary saves and checkpoints. The gameplay
registry still needs to build native pets from those records and test
combat, movement, and restart. Pet inventory requires a separate bounded
serialization path.
