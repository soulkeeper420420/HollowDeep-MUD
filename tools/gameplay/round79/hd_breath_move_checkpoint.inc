/* Round 79J: one atomic checkpoint of the player's moved room and
 * revisioned Breath receipt. Includes only in hd_player_store.c after
 * hd_breath_store.inc with HD79_BREATH_MOVE_CHECKPOINT_TEST enabled.
 *
 * DO NOT call this after arbitrary movement until native exit validation,
 * successful-move gating and failure rollback are separately proven.
 */
#ifndef HD79_BREATH_STORE_PLAYTEST
#error "Native room+Breath checkpoint requires Breath receipt storage"
#endif
#include "hd_breath_move_checkpoint.h"

int hd_breath_store_checkpoint_move(
    const char *name, creature *moved_player,
    int previous_room, const hd_breath_record *expected,
    int wilderness, uint32_t now, hd_breath_record *out)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set receipts;
    hd_breath_record prior,next;
    char before[65],wire[65];
    creature snapshot,*disk;
    otag worn[MAXWEAR];
    size_t used=0,native=0,total=0,expected_size=0;
    int i,idx,serialized,packed_len,lock=-1,wr;
    int result=HD_BREATH_STORE_FAILURE;

    /* A complete successful move must be present in live player memory.
     * Only a separately verified native exit resolver decides whether
     * the destination is a real wilderness tile.
     */
    if (!out || !expected || !moved_player || !valid_name(name) ||
        !native_name(moved_player->name,name) ||
        moved_player->type!=PLAYER ||
        moved_player->level<1 || moved_player->level>60 ||
        previous_room<0 || previous_room>=RMAX ||
        moved_player->rom_num<0 || moved_player->rom_num>=RMAX ||
        previous_room==moved_player->rom_num ||
        (wilderness!=0 && wilderness!=1) ||
        !hd_breath_record_valid(expected))
        return result;

    snapshot=*moved_player;
    /* Duplicate the existing native live-save equipment normalization.
     * The copy does not mutate the actual player or worn items.
     */
    for (i=0;i<MAXWEAR;++i) {
        if (!snapshot.ready[i]) continue;
        worn[i].obj=snapshot.ready[i];
        worn[i].next_tag=snapshot.first_obj;
        snapshot.first_obj=&worn[i];
        snapshot.ready[i]=NULL;
    }
    if (native_size(&snapshot,&expected_size)) return result;

    raw=(unsigned char *)malloc(HD_RAW_CAPACITY);
    packed=(unsigned char *)malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;

    /* Exactly the existing player store lock, so saving in another
     * process, pet/Conjure mutations, or movement cannot race this
     * receipt and room checkpoint.
     */
    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (lock<0 || flock(lock,LOCK_EX)<0 ||
        read_record(name,raw,&used,&native,&receipts))
        goto done;
    disk=(creature *)raw;
    if (disk->type!=PLAYER || disk->rom_num!=previous_room ||
        !native_name(disk->name,name)) {
        result=HD_BREATH_STORE_CONFLICT;
        goto done;
    }
    idx=hd_breath_entry(&receipts);
    if (idx<0) {
        result=HD_BREATH_STORE_CONFLICT;
        goto done;
    }
    if (hd_breath_record_decode(
            receipts.entries[idx].manifest_sha256,&prior) ||
        hd_breath_record_encode(expected,before))
        goto done;
    if (strcmp(before,receipts.entries[idx].manifest_sha256)) {
        result=HD_BREATH_STORE_CONFLICT;
        goto done;
    }
    if (hd_breath_record_step(
            &prior,&next,HD_BREATH_OP_TRAVEL,wilderness,0,now))
        goto done;

    if (hd_breath_record_encode(&next,wire)) goto done;
    memcpy(receipts.entries[idx].manifest_sha256,wire,65);

    serialized=write_crt_to_mem((char *)raw,&snapshot,0);
    if (serialized<0 || (size_t)serialized!=expected_size)
        goto done;
    if (hd_receipt_encode(
            raw,HD_RAW_CAPACITY,expected_size,&receipts,&total))
        goto done;
    packed_len=hd_compress_bounded(
        (char *)raw,(char *)packed,(int)total,HD_PLAYER_COMPRESSED_LIMIT);
    if (packed_len<1 || packed_len>(int)HD_PLAYER_COMPRESSED_LIMIT)
        goto done;
    wr=hd_atomic_player_snapshot(
        PLAYERPATH,name,packed,(size_t)packed_len);
    if (wr==HD_SNAPSHOT_OK || wr==HD_SNAPSHOT_UNCERTAIN) {
        *out=next;
        result=wr==HD_SNAPSHOT_OK ? HD_BREATH_STORE_OK :
                                      HD_BREATH_STORE_UNCERTAIN;
    }
done:
    if (lock>=0) { flock(lock,LOCK_UN); close(lock); }
    free(raw);
    free(packed);
    return result;
}
