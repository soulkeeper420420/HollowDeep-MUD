# Necromancer roster codec

This is the fixed-width roster payload for the private Undead Army work.
The current single-pet store remains the gameplay entry point.

The payload preserves the character epoch and revision and records each
living pet's stable ID, monster template, level, room, HP, MP, XP and stay
flag. The allocator's next ID is persisted separately so a later save can
remove a pet without recycling its ID. Records are ordered by increasing
pet ID. The versioned payload uses big-endian integers and has a maximum
size of 368 bytes. Decoding requires the exact length and validates the
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

Next, integrate the payload with the locked native player transaction. The
save reader and ordinary saves will need to preserve an optional roster
section alongside existing treasure receipts. Validate revision changes,
never reuse a pet ID after deletion, and preserve the original receipt
until the first successful roster commit. Carry variable-sized pet
inventory through the native bounded serializer. Commit resources, rewards
and roster state together before making their effects visible. Verify the
existing ELF32 socket replay and add multi-pet end-to-end cases before
using the new section in gameplay.
