/* Included inside the native locked player store. */
#include "hd_conjure.c"

/* Exactly 32 encoded bytes, independent of the undead roster. */
static int cj_encode(const hd_conjure_state *s, char out[65])
{
    if (!hd_conjure_valid(s) || !s->revision ||
        !pet_hex(s->epoch,24) ||
        !strcmp(s->epoch,"000000000000000000000000"))
        return -1;

    return snprintf(out,65,
        "01%s%08lx%08lx%08lx%02x%02x%04x%04x%02x",
        s->epoch,(unsigned long)s->revision,
        (unsigned long)s->last_cast,(unsigned long)s->xp,
        s->species,s->active,s->hp,s->mp,s->level)==64 ? 0:-1;
}

static int cj_decode(const char *wire, hd_conjure_state *out)
{
    hd_conjure_state s = {0};
    char check[65];

    if (!pet_hex(wire,64) || memcmp(wire,"01",2))
        return -1;

    memcpy(s.epoch,wire+2,24);
    s.revision = pet_num(wire+26,8);
    s.last_cast = pet_num(wire+34,8);
    s.xp = pet_num(wire+42,8);
    s.species = pet_num(wire+50,2);
    s.active = pet_num(wire+52,2);
    s.hp = pet_num(wire+54,4);
    s.mp = pet_num(wire+58,4);
    s.level = pet_num(wire+62,2);

    if (cj_encode(&s,check) || strcmp(check,wire))
        return -1;

    *out = s;
    return 0;
}

static int cj_entry(const hd_receipt_set *set)
{
    size_t i;
    for (i=0;i<set->count;++i)
        if (!strcmp(set->entries[i].claim_id,conjure_id))
            return (int)i;
    return -1;
}

int hd_conjure_store_read(const char *name,
                          hd_conjure_state *out)
{
    unsigned char *raw;
    hd_receipt_set set;
    size_t used,native;
    int idx,result=HD_PET_ERROR;

    if (!out || !valid_name(name)) return result;
    raw=malloc(HD_RAW_CAPACITY);
    if (!raw) return result;

    if (!read_record(name,raw,&used,&native,&set) &&
        ((creature *)raw)->type==PLAYER) {
        idx=cj_entry(&set);
        result=idx<0 ? HD_PET_ABSENT :
            cj_decode(set.entries[idx].manifest_sha256,out);
    }

    free(raw);
    return result;
}

int hd_conjure_store_apply(
    const char *name, const hd_conjure_state *expected,
    unsigned action, uint32_t now,
    unsigned a, unsigned b, hd_conjure_state *out)
{
    unsigned char *raw=NULL,*packed=NULL;
    hd_receipt_set set;
    hd_conjure_state next;
    char before[65],wire[65];
    size_t used,native,total;
    int idx,lock=-1,length,result=HD_PET_ERROR;
    creature *owner;

    if (!out || !valid_name(name)) return result;
    raw=malloc(HD_RAW_CAPACITY);
    packed=malloc(HD_PLAYER_COMPRESSED_LIMIT);
    if (!raw || !packed) goto done;

    lock=open(PLAYERPATH,O_RDONLY|O_DIRECTORY|
                          O_NOFOLLOW|O_CLOEXEC);

    if (lock<0 || flock(lock,LOCK_EX) ||
        read_record(name,raw,&used,&native,&set))
        goto done;

    owner=(creature *)raw;
    if (owner->type!=PLAYER ||
        owner->level<1 || owner->level>60)
        goto done;

    idx=cj_entry(&set);

    if (action==HD_CJ_INIT) {
        if (expected) goto done;
        if (idx>=0) {
            if (!cj_decode(set.entries[idx].manifest_sha256,out))
                result=HD_PET_CONFLICT;
            goto done;
        }

        memset(&next,0,sizeof next);
        next.revision=1;
        if (pet_epoch(next.epoch)) goto done;
    } else {
        if (idx<0 || !expected) {
            result=HD_PET_CONFLICT;
            goto done;
        }

        if (cj_decode(set.entries[idx].manifest_sha256,&next) ||
            cj_encode(expected,before))
            goto done;

        if (strcmp(before,set.entries[idx].manifest_sha256)) {
            result=HD_PET_CONFLICT;
            goto done;
        }

        if (next.revision==UINT32_MAX ||
            hd_conjure_step(&next,action,
                            owner->level,now,a,b))
            goto done;

        ++next.revision;
    }

    if (cj_encode(&next,wire)) goto done;

    if (idx<0) {
        if (hd_receipt_add(&set,conjure_id,wire))
            goto done;
    } else {
        memcpy(set.entries[idx].manifest_sha256,wire,65);
    }

    if (hd_receipt_encode(raw,HD_RAW_CAPACITY,native,
                          &set,&total))
        goto done;

    length=hd_compress_bounded((char *)raw,(char *)packed,
                               (int)total,
                               HD_PLAYER_COMPRESSED_LIMIT);

    if (length<1 || length>HD_PLAYER_COMPRESSED_LIMIT)
        goto done;

    idx=hd_atomic_player_snapshot(
        PLAYERPATH,name,packed,(size_t)length);

    if (idx==HD_SNAPSHOT_OK ||
        idx==HD_SNAPSHOT_UNCERTAIN) {
        *out=next;
        result=idx==HD_SNAPSHOT_OK ?
            HD_PET_OK : HD_PET_UNCERTAIN;
    }

done:
    if (lock>=0) close(lock);
    free(raw);
    free(packed);
    return result;
}
