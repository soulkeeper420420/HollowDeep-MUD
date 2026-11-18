#include "hd_player_store.h"
#include "mextern.h"
#include "hd_pet_store.h"
#include "hd_necro_skeleton.h"
#include "hd_conjure.h"
#include "hd_conjure_runtime.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>

typedef struct {
    creature *owner, *pet;
    hd_conjure_state saved;
    uint32_t last_hit, last_drain;
} cj_session;

static cj_session slots[PMAX];

static void cj_stop(const char *where,int result)
{
    fprintf(stderr,"Private Conjure error: %s (%d)\n",
            where,result);
    _exit(74);
}

static uint32_t cj_now(void)
{
    time_t now=time(NULL);
    if(now<=0 || (uintmax_t)now>UINT32_MAX)
        cj_stop("clock",-1);
    return (uint32_t)now;
}

static cj_session *by_owner(creature *owner)
{
    size_t i;
    if(!owner) return NULL;
    for(i=0;i<PMAX;++i)
        if(slots[i].owner==owner)
            return &slots[i];
    return NULL;
}

static cj_session *by_pet(creature *pet)
{
    size_t i;
    if(!pet) return NULL;
    for(i=0;i<PMAX;++i)
        if(slots[i].pet==pet)
            return &slots[i];
    return NULL;
}

int hd_cj_is_pet(creature *pet)
{
    return by_pet(pet)!=NULL;
}

static void apply(cj_session *s,unsigned action,
                  unsigned a,unsigned b)
{
    int rc=hd_conjure_store_apply(
        s->owner->name,&s->saved,action,
        cj_now(),a,b,&s->saved);

    if(rc!=HD_PET_OK)
        cj_stop("atomic companion update",rc);
}

static void sync_vitals(cj_session *s)
{
    if(!s->pet) return;

    if(s->pet->hpcur<1 || s->pet->mpcur<0)
        cj_stop("invalid live companion",-1);

    if(s->saved.hp!=(unsigned)s->pet->hpcur ||
       s->saved.mp!=(unsigned)s->pet->mpcur)
        apply(s,HD_CJ_VITALS,
              s->pet->hpcur,s->pet->mpcur);
}

static void detach(creature *pet)
{
    if(pet->parent_rom) {
        del_active(pet);
        del_crt_rom(pet,pet->parent_rom);
    }
}

static void destroy(cj_session *s)
{
    creature *pet=s->pet;
    s->pet=NULL;

    if(pet) {
        detach(pet);
        free_crt(pet);
    }
}

static void update_pet(cj_session *s)
{
    creature *pet=s->pet;

    pet->level=s->saved.level;
    pet->hpmax=hd_conjure_hp(
        s->saved.species,s->saved.level);
    pet->mpmax=hd_conjure_mp(
        s->saved.species,s->saved.level);
    pet->hpcur=s->saved.hp;
    pet->mpcur=s->saved.mp;
}

static void materialize(cj_session *s)
{
    creature *pet;
    const hd_conjure_template *t;

    if(s->pet || !s->saved.active ||
       !s->owner->parent_rom)
        return;

    t=hd_conjure_get(s->saved.species);

    if(!t || s->owner->level<t->unlock ||
       s->owner->level<s->saved.level)
        return;

    pet=calloc(1,sizeof *pet);
    if(!pet) cj_stop("allocation",-1);

    strcpy(pet->name,t->name);
    strcpy(pet->description,"A conjured companion.");
    pet->type=MONSTER;
    pet->class=FIGHTER;
    pet->fd=-1;
    pet->strength=t->strength;
    pet->dexterity=t->dexterity;
    pet->constitution=t->constitution;
    pet->intelligence=t->intelligence;
    pet->piety=t->piety;
    pet->ndice=1;
    pet->sdice=4;

    F_SET(pet,MNRGLD);

    s->pet=pet;
    update_pet(s);
    add_crt_rom(pet,s->owner->parent_rom,0);
}

static cj_session *load_session(creature *owner,int create)
{
    cj_session *s;
    hd_conjure_state saved;
    size_t i;
    int rc;

    if(!owner || owner->type!=PLAYER ||
       !owner->parent_rom || owner->level<1 ||
       owner->level>60)
        return NULL;

    s=by_owner(owner);
    if(s) return s;

    rc=hd_conjure_store_read(owner->name,&saved);

    if(rc==HD_PET_ABSENT && !create)
        return NULL;

    if(rc==HD_PET_ABSENT) {
        if(hd_store_save_live_player(owner->name,owner))
            cj_stop("initial owner save",-1);

        rc=hd_conjure_store_apply(
            owner->name,NULL,HD_CJ_INIT,
            0,0,0,&saved);
    }

    if(rc!=HD_PET_OK)
        cj_stop("load companion",rc);

    for(i=0;i<PMAX;++i)
        if(!slots[i].owner) break;

    if(i==PMAX) cj_stop("session capacity",-1);

    s=&slots[i];
    s->owner=owner;
    s->saved=saved;

    /* Preserve progress if a rebirthed owner is below
       the companion's required level. */
    if(saved.active &&
       (owner->level<saved.level ||
        owner->level<hd_conjure_get(saved.species)->unlock))
        apply(s,HD_CJ_DISMISS,0,0);

    materialize(s);
    return s;
}

void hd_cj_login(creature *owner)
{
    load_session(owner,0);
}

void hd_cj_logout(creature *owner)
{
    cj_session *s=by_owner(owner);
    if(!s) return;

    sync_vitals(s);
    destroy(s);
    memset(s,0,sizeof *s);
}

int hd_cj_death(creature *pet)
{
    cj_session *s=by_pet(pet);

    if(!s) return 0;

    apply(s,HD_CJ_DEATH,0,0);
    s->pet=NULL;
    s->last_hit=s->last_drain=0;

    print(s->owner->fd,
          "Your conjured companion has been lost forever.\n");
    return 1;
}

void hd_cj_follow(creature *owner,room *where)
{
    cj_session *s=by_owner(owner);

    if(!s || !s->pet || !where ||
       owner->parent_rom!=where)
        return;

    if(s->pet->parent_rom!=where) {
        detach(s->pet);
        add_crt_rom(s->pet,where,0);
    }
}

void hd_cj_tick(void)
{
    size_t i;
    for(i=0;i<PMAX;++i)
        if(slots[i].owner)
            hd_cj_follow(slots[i].owner,
                         slots[i].owner->parent_rom);
}

void hd_cj_checkpoint_all(void)
{
    size_t i;
    for(i=0;i<PMAX;++i)
        if(slots[i].owner)
            sync_vitals(&slots[i]);
}

void hd_cj_unload(room *where)
{
    size_t i;
    for(i=0;i<PMAX;++i)
        if(slots[i].pet &&
           slots[i].pet->parent_rom==where) {
            sync_vitals(&slots[i]);
            detach(slots[i].pet);
        }
}

void hd_cj_status(creature *owner)
{
    cj_session *s=load_session(owner,0);
    const hd_conjure_template *t;
    char line[240];

    if(!s || !s->saved.species) {
        print(owner->fd,"Companion: none (0/1).\n");
        return;
    }

    t=hd_conjure_get(s->saved.species);
    sync_vitals(s);

    snprintf(line,sizeof line,
       "Companion: %s | Level %u | XP %lu | HP %u/%u | MP %u/%u | %s\n",
       t->name,s->saved.level,
       (unsigned long)s->saved.xp,
       s->saved.hp,hd_conjure_hp(s->saved.species,s->saved.level),
       s->saved.mp,hd_conjure_mp(s->saved.species,s->saved.level),
       s->saved.active?"active":"dismissed");

    print(owner->fd,"%s",line);
}

int hd_cj_assist(creature *owner,creature *target)
{
    cj_session *s=by_owner(owner);
    creature *pet;
    uint32_t now;
    int damage,limit;
    char line[220];

    if(!s || !(pet=s->pet) || !target ||
       target->type!=MONSTER || target->hpcur<1 ||
       !owner->parent_rom ||
       owner->parent_rom!=target->parent_rom ||
       pet->parent_rom!=owner->parent_rom ||
       hd_necro_skeleton_is_pet(target) ||
       F_ISSET(target,MUNKIL) ||
       F_ISSET(target,MMGONL) ||
       F_ISSET(target,MTRADE) ||
       F_ISSET(target,MDMFOL) ||
       !is_enm_crt(owner->name,target))
        return 0;

    now=cj_now();

    if(s->last_hit && now>=s->last_hit &&
       now-s->last_hit<3)
        return 0;

    s->last_hit=now;

    /* Preserve the permanent-monster finishing restriction. */
    limit=target->hpcur;
    if(F_ISSET(target,MPERMT)) --limit;

    if(limit<1) return 0;

    damage=MIN(4+pet->level/2,limit);

    if(s->saved.species==5 &&
       target->mpcur>0 && target->mpmax>0) {
        unsigned a,b,drained;

        drained=hd_conjure_drain(
            mrand(1,100),
            target->mpcur,target->mpmax,
            MAX(0,owner->mpmax-owner->mpcur),
            MAX(0,pet->mpmax-pet->mpcur),
            now,&s->last_drain,&a,&b);

        if(drained) {
            target->mpcur-=drained;
            owner->mpcur+=a;
            pet->mpcur+=b;
            sync_vitals(s);

            snprintf(line,sizeof line,
                "Your shadow wraith drains %u mana.\n",
                drained);
            print(owner->fd,"%s",line);
        }
    }

    target->hpcur-=damage;
    add_enm_dmg(owner->name,target,damage);

    snprintf(line,sizeof line,
             "Your %s hits for %d damage.\n",
             pet->name,damage);
    print(owner->fd,"%s",line);

    if(!target->hpcur) {
        unsigned xp=0;

        if(target->experience>0)
            xp=(unsigned)target->experience;

        sync_vitals(s);

        if(xp) {
            /* Synchronize owner level before storage validates
               the companion's permitted progression. */
            if(hd_store_save_live_player(owner->name,owner))
                cj_stop("owner progression save",-1);

            apply(s,HD_CJ_XP,xp,0);
            update_pet(s);
        }

        snprintf(line,sizeof line,
                "Your %s finishes %s and earns %u XP.\n",
                pet->name,target->name,xp);
        print(owner->fd,"%s",line);

        /* Native owner XP and corpse rewards. */
        die(target,owner);
        return 1;
    }

    return 0;
}

int hd_cj_command(creature *owner,cmd *command)
{
    cj_session *s;
    hd_conjure_state preview;
    const hd_conjure_template *t;
    char verb[16],arg[32],target_name[80],extra[2],line[220];
    unsigned id,operation;
    uint32_t now;
    int words;

    if(!owner || owner->type!=PLAYER ||
       !owner->parent_rom || !command)
        return 0;

    words=sscanf(command->fullstr,
       "%15s %31s %79s %1s",
       verb,arg,target_name,extra);

    if(words==2 && !strcasecmp(arg,"list")) {
        for(id=1;id<=6;++id) {
            t=hd_conjure_get(id);
            snprintf(line,sizeof line,
                "Level %u: %s (%s)%s\n",
                t->unlock,t->name,t->key,
                owner->level<t->unlock?" [locked]":"");
            print(owner->fd,"%s",line);
        }
        return 0;
    }

    if(words==1 ||
       (words==2 && !strcasecmp(arg,"status"))) {
        hd_cj_status(owner);
        return 0;
    }

    if(words==3 && !strcasecmp(arg,"attack")) {
        creature *target=find_crt(owner,
            owner->parent_rom->first_mon,target_name,1);

        if(!target || !is_enm_crt(owner->name,target)) {
            print(owner->fd,
                  "Choose a monster you are already fighting.\n");
            return 0;
        }

        hd_cj_assist(owner,target);
        return 0;
    }


    if(words==3 && !strcasecmp(arg,"release") &&
       !strcasecmp(target_name,"confirm")) {
        s=load_session(owner,0);

        if(!s || !s->saved.species || s->saved.active) {
            print(owner->fd,"Dismiss your companion before releasing it.\n");
            return 0;
        }

        apply(s,HD_CJ_RELEASE,0,0);
        print(owner->fd,"Your companion has been permanently released.\n");
        return 0;
    }

    if(words!=2) goto usage;

    if(!strcasecmp(arg,"dismiss")) {
        s=by_owner(owner);

        if(!s || !s->pet) {
            print(owner->fd,"No active companion.\n");
            return 0;
        }

        sync_vitals(s);
        apply(s,HD_CJ_DISMISS,0,0);
        destroy(s);

        print(owner->fd,
              "Companion dismissed. Its progress is saved.\n");
        return 0;
    }

    id=0;

    if(!strcasecmp(arg,"recall")) {
        operation=HD_CJ_RECALL;
    } else {
        operation=HD_CJ_SUMMON;

        for(id=1;id<=6;++id)
            if(!strcasecmp(arg,hd_conjure_get(id)->key))
                break;

        if(id>6) goto usage;

        if(owner->level<hd_conjure_get(id)->unlock) {
            print(owner->fd,
                  "That companion is not unlocked yet.\n");
            return 0;
        }
    }

    s=load_session(owner,operation==HD_CJ_SUMMON);

    if(!s) {
        print(owner->fd,"No saved companion.\n");
        return 0;
    }

    if(s->saved.active ||
       (operation==HD_CJ_SUMMON && s->saved.species)) {
        print(owner->fd,
              "You already have a companion.\n");
        return 0;
    }

    now=cj_now();

    if(s->saved.last_cast &&
       (now<s->saved.last_cast ||
        now-s->saved.last_cast<HD_CONJURE_COOLDOWN)) {

        unsigned remaining=now<s->saved.last_cast?
            HD_CONJURE_COOLDOWN:
            HD_CONJURE_COOLDOWN-(now-s->saved.last_cast);

        snprintf(line,sizeof line,
                 "Conjure is ready in %u seconds.\n",remaining);
        print(owner->fd,"%s",line);
        return 0;
    }

    preview=s->saved;

    if(hd_conjure_step(&preview,operation,
                      owner->level,now,id,0)) {
        print(owner->fd,"You cannot conjure that companion.\n");
        return 0;
    }

    if(hd_store_save_live_player(owner->name,owner))
        cj_stop("summon owner save",-1);

    apply(s,operation,id,0);
    materialize(s);

    snprintf(line,sizeof line,"You conjure %s.\n",
             hd_conjure_get(s->saved.species)->name);
    print(owner->fd,"%s",line);
    return 0;

usage:
    print(owner->fd,
        "Use conjure list, conjure <type>, conjure status,\n"
        "conjure dismiss, conjure recall, or conjure attack <monster>.\n");
    return 0;
}
