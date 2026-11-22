/* Round79T: canonical 64-byte mount record -> two 64-hex receipts.
 * PURE serializer; does not choose claim IDs or write save data.
 * A future native transaction must atomically replace BOTH reserved
 * receipt values in one snapshot, with epoch+revision CAS.
 * Layout (big endian, version 1):
 * 0 magic 0x4d; 1 version=1; 2 count; 3 active_id;
 * 4..15 epoch bytes; 16..19 revision;
 * 20..55 six entries: species, endurance, stabled, stable_room[24];
 * 56..59 CRC32 of bytes 0..55; 60..63 zero reserved.
 */
#ifndef HD79_MOUNT_WIRE_H
#define HD79_MOUNT_WIRE_H
#include "hd79_mount_roster.h"
#define HD79_MOUNT_RECEIPT_HEX 64U
#define HD79_MOUNT_RECEIPTS 2U
#define HD79_MOUNT_WIRE_BYTES 64U
#define HD79_MOUNT_MAX_STABLE_ROOM 0xffffffU

/* 0 success, -1 failure; never change outputs on failure. Each
 * output is NUL-terminated, 64 lower-case hex digits.
 * Pair must be stored atomically in the native receipt set.
 */
int hd79_mount_wire_encode(const hd79_mount_roster *roster,
                           char first[65], char second[65]);
int hd79_mount_wire_decode(const char *first,const char *second,
                           hd79_mount_roster *out);
#endif
