/* Private synthetic socket fixture only. Never link into a release build. */
#if !defined(HD79_AD_SOCKET_TESTING) || !defined(HD_ATOMIC_TESTING) || \
    !defined(HD79_AD_FOUR_STORE_TESTING)
#error "Disposable socket fixture requires all three explicit test switches"
#endif
#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_ad_private_fleet.h"
#include "hd79_ad_four_store.h"
#include "hd79_ad_species.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int hd79_ad_socket_fixture(creature *owner,cmd *command)
{
    hd79_mount_roster r,nr;
    hd79_mount_presence p,np;
    hd79_ad_death_receipt d,nd;
    creature *mount=NULL;
    char verb[20],action[20],extra;
    unsigned id=0,i;
    int rc;
    /* The replay creates only this disposable player in its own chroot. */
    if(!owner || owner->type!=PLAYER || strcmp(owner->name,"Hdnecroqa") ||
       owner->rom_num!=2 || !owner->parent_rom || owner->hpcur<=0 ||
       !command) return 0;
    if(sscanf(command->fullstr,"%19s %19s %u %c",verb,action,&id,&extra)<2 ||
       strcmp(verb,"adfixture")) return 0;
    rc=hd79_ad_four_store_read(owner->name,&r,&p,&d);
    if(!strcmp(action,"seed") && rc==HD79_AD_FOUR_ABSENT) {
        if(hd79_ad_four_store_init_empty(owner->name,&r,&p,&d)!=HD79_AD_FOUR_OK)
            goto denied;
        for(i=1;i<=6;i++) {
            if(hd79_ad_four_store_test_award(owner->name,&r,&p,&d,(int)i,
                    2,&nr,&np,&nd)!=HD79_AD_FOUR_OK) goto denied;
            r=nr;p=np;d=nd;
        }
        print(owner->fd,"AD FIXTURE SEEDED six synthetic owned mounts.\n");
        return 0;
    }
    if(rc!=HD79_AD_FOUR_OK) goto denied;
    if(!strcmp(action,"failbefore") || !strcmp(action,"failafter")) {
        setenv("HD_ATOMIC_FAIL",!strcmp(action,"failbefore") ?
               "before_rename":"after_rename",1);
        print(owner->fd,"AD FIXTURE FAULT ARMED.\n");
        return 0;
    }
    if(!strcmp(action,"clear")) {
        unsetenv("HD_ATOMIC_FAIL");
        print(owner->fd,"AD FIXTURE FAULT CLEARED.\n");
        return 0;
    }
    if(!strcmp(action,"pending")) {
        ctag *tag;
        unsigned matches=0;
        for(tag=owner->parent_rom->first_mon;tag;tag=tag->next_tag)
            if(tag->crt && !strcmp(tag->crt->key[0],"adtarget") &&
               tag->crt->hpcur<=0) matches++;
        print(owner->fd,"AD FIXTURE pending=%u.\n",matches);
        return 0;
    }
    if(!strcmp(action,"status")) {
        print(owner->fd,"AD FIXTURE mask=%u serial=%u count=%u.\n",
              d.dead_mask,d.serial,r.count);
        return 0;
    }
    if(!strcmp(action,"spawn") && id>=1 && id<=6) {
        rc=hd79_ad_private_spawn(owner,id,&mount);
        if(rc!=1) goto denied;
        {
            const hd79_ad_species_profile *s=hd79_ad_species_get(
                r.entries[id-1].species);
            if(!s || mount->level!=s->level || mount->hpcur!=s->hp ||
               mount->hpmax!=s->hp || mount->ndice!=s->dice ||
               mount->sdice!=s->sides || mount->pdice!=s->plus ||
               strcmp(mount->key[0],s->key)) goto denied;
            print(owner->fd,"AD NATIVE DEFINITION level=%u hp=%u dice=%ud%u+%u.\n",
                s->level,s->hp,s->dice,s->sides,s->plus);
        }
        /* A deterministic combat target, not a live gameplay definition. */
        strcpy(mount->key[0],"adtarget");
        mount->hpcur=1;
        mount->armor=0;
        owner->thaco=1;
        print(owner->fd,"AD FIXTURE SPAWNED #%u.\n",id);
        return 0;
    }
denied:
    print(owner->fd,"AD FIXTURE DENIED.\n");
    return 0;
}
