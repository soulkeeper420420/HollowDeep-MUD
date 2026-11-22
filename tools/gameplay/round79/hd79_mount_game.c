#include "hd_player_store.h"
#include "mextern.h"
#include "hd79_breath_travel_runtime.h"
#include "hd_breath_store.h"
#include "hd79_mount_store.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

extern int hd79_wilderness_terrain(int);

int hd79_mount_stable_room(int room_id)
{
    FILE *file;
    struct stat st;
    char line[32],*end;
    long room;
    unsigned rooms[128],count=0,i;
    int found=0,fd;
    fd=open(ROOMPATH "/stables.map",O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return 0;
    if (fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_uid!=geteuid() ||
        (st.st_mode & 0022)) { close(fd); return 0; }
    file=fdopen(fd,"r");
    if (!file) { close(fd); return 0; }
    if (!fgets(line,sizeof line,file) || strcmp(line,"HDSTABLE1\n")) goto bad;
    while (fgets(line,sizeof line,file)) {
        if (count>=128 || !strchr(line,'\n') || line[0]<'0' || line[0]>'9') goto bad;
        errno=0; room=strtol(line,&end,10);
        if (errno || strcmp(end,"\n") || room<1 || room>=RMAX) goto bad;
        for (i=0;i<count;++i) if (rooms[i]==(unsigned)room) goto bad;
        rooms[count++]=(unsigned)room;
        if (room==room_id) found=1;
    }
    if (ferror(file)) goto bad;
    fclose(file); return found;
bad:
    fclose(file); return 0;
}

static int read_roster(creature *player,hd79_mount_roster *out)
{
    int current;
    if (!player || player->type!=PLAYER || player->class>=CARETAKER ||
        hd79_breath_status(player,&current)) return -1;
    return hd79_mount_read(player->name,out);
}

/* After uncertain rename, confirm both the canonical pair and native fields.
 * A failed reconciliation drops the session before it can overwrite the disk. */
static int commit(creature *player,const hd79_mount_roster *before,
                  unsigned operation,unsigned value,unsigned stable,
                  int wilderness,const hd_travel_plan *plan)
{
    hd79_mount_roster next,actual;
    creature *disk=NULL;
    char a[65],b[65],c[65],d[65];
    int rc,ok=0;
    long gold=player->gold-(operation==HD79_MOUNT_BUY ? 100L*value:0);
    int room=operation==HD79_MOUNT_MOVE ? (int)value:player->rom_num;
    rc=hd79_mount_change(player,before,operation,value,stable,wilderness,plan,&next);
    if (rc==HD79_MOUNT_UNCERTAIN) {
        if (hd79_mount_read(player->name,&actual)==HD79_MOUNT_OK &&
            !hd79_mount_wire_encode(&actual,a,b) && !hd79_mount_wire_encode(&next,c,d) &&
            !strcmp(a,c) && !strcmp(b,d) &&
            hd_store_load_player(player->name,&disk)==HD_STORE_OK && disk &&
            disk->rom_num==room && disk->gold==gold)
            ok=1;
        if (disk) free_crt(disk);
        if (!ok) {
            print(player->fd,"Mount save requires recovery. Reconnect before acting.\n");
            /* Avoid the normal disconnect save overwriting an uncertain image. */
            player->fd=-1;
            return -2;
        }
        rc=HD79_MOUNT_OK;
    }
    if (rc!=HD79_MOUNT_OK) return -1;
    player->gold=gold;
    return 0;
}

static unsigned mount_number(const char *s)
{
    char *end;
    unsigned long n;
    if (!s || !s[0] || strlen(s)>1 || s[0]<'1' || s[0]>'6') return 0;
    n=strtoul(s,&end,10);
    return *end ? 0:(unsigned)n;
}

int hd79_mount_command(creature *player,cmd *command)
{
    hd79_mount_roster state;
    unsigned value=0,operation=0,i;
    int rc;
    if (read_roster(player,&state)<0) {
        print(player->fd,"Your mount record cannot be verified.\n"); return 0;
    }
    if (!strcmp(command->str[0],"mounts") ||
        (!strcmp(command->str[0],"stable") && command->num==1)) {
        print(player->fd,"Owned mounts: %u/6. Riding: %u.\n",state.count,state.active_id);
        for (i=0;i<state.count;++i) {
            hd79_owned_mount *m=&state.entries[i];
            print(player->fd,"%u %s Endurance %u/%u%s",
                  m->id,hd_mount_get(m->species)->name,m->endurance,
                  hd_mount_get(m->species)->endurance_max,m->stabled ? " stabled":" present");
            if (m->stabled) print(player->fd," at room %u",m->stable_room);
            print(player->fd,"\n");
        }
        print(player->fd,"Stable buy <species 1..6>: 100 gold times species. Stable deposit/retrieve <id>.\n");
        return 0;
    }
    if (!strcmp(command->str[0],"dismount") && command->num==1) operation=HD79_MOUNT_OFF;
    else if (!strcmp(command->str[0],"mount") && command->num==2) {
        operation=HD79_MOUNT_BOARD; value=mount_number(command->str[1]);
    } else if (!strcmp(command->str[0],"stable") && command->num==3) {
        value=mount_number(command->str[2]);
        if (!strcmp(command->str[1],"buy")) operation=HD79_MOUNT_BUY;
        if (!strcmp(command->str[1],"deposit")) operation=HD79_MOUNT_DEPOSIT;
        if (!strcmp(command->str[1],"retrieve")) operation=HD79_MOUNT_RETRIEVE;
    }
    if (!operation || (operation!=HD79_MOUNT_OFF && !value)) {
        print(player->fd,"Use mounts, mount <id>, dismount, or stable buy/deposit/retrieve <id>.\n");
        return 0;
    }
    rc=commit(player,&state,operation,value,(unsigned)player->rom_num,0,NULL);
    if (rc==-2) return DISCONNECT;
    print(player->fd,rc==0 ? "Mount change saved.\n":"Mount action denied or save failed.\n");
    return 0;
}

/* 1 handled mounted move, 0 foot, -1 blocked. Native exit checks run first. */
int hd79_mount_precommit(creature *player,room *destination)
{
    hd79_mount_roster state;
    hd_breath_record breath;
    hd_travel_plan plan;
    hd79_owned_mount *mount;
    int wild,terrain=0,rc,fd=player->fd;
    if (read_roster(player,&state)<0) return -1;
    if (!state.active_id) return 0;
    wild=hd79_wilderness_tile(destination->rom_num);
    if (wild<0) return -1;
    if (wild) {
        terrain=hd79_wilderness_terrain(destination->rom_num);
        if (terrain<0) return -1;
    }
    if (hd_breath_store_read(player->name,&breath)!=HD_BREATH_STORE_OK) return -1;
    mount=&state.entries[state.active_id-1];
    if (hd_mount_travel_preview(mount->species,wild,(char)terrain,breath.current,mount->endurance,&plan)!=1) {
        print(player->fd,"Your mount cannot cross this terrain or lacks Endurance.\n");
        return -1;
    }
    rc=commit(player,&state,HD79_MOUNT_MOVE,(unsigned)destination->rom_num,0,wild,&plan);
    if (rc) {
        if (rc==-2) {
            output_buf();
            disconnect(fd);
        } else {
            print(player->fd,"Mounted travel could not be saved.\n");
        }
        return -1;
    }
    return 1;
}
