#include "hd79_mount_roster.h"
#include <string.h>
int hd79_mount_roster_valid(const hd79_mount_roster *r) {
 unsigned i;
 if(!r || strlen(r->epoch)!=24 || !r->revision || r->count>6 || r->active_id>r->count) return 0;
 for(i=0;i<r->count;i++) {
  if(r->entries[i].id!=i+1 || !r->entries[i].species ||
    (r->entries[i].stabled && (!r->entries[i].stable_room || r->active_id==i+1)) ||
    (!r->entries[i].stabled && r->entries[i].stable_room))return 0;
 }
 return 1;
}
int hd79_mount_roster_new(hd79_mount_roster *out,const char *e) {
 if(!out||!e||strlen(e)!=24)return -1;
 memset(out,0,sizeof *out);strcpy(out->epoch,e);out->revision=1;return 1;
}
int hd79_mount_board(const hd79_mount_roster *r,hd79_mount_roster *n,const char *e,unsigned id,int present) {
 if(!hd79_mount_roster_valid(r)||!n||strcmp(r->epoch,e)||!id||id>r->count)return -1;
 if(!present||r->active_id||r->entries[id-1].stabled)return 0;
 if(r->revision==UINT32_MAX)return -1;
 *n=*r;n->active_id=id;n->revision++;return 1;
}
int hd79_mount_dismount(const hd79_mount_roster *r,hd79_mount_roster *n,const char *e) {
 if(!hd79_mount_roster_valid(r)||!n||strcmp(r->epoch,e))return -1;
 if(!r->active_id)return 0;
 if(r->revision==UINT32_MAX)return -1;
 *n=*r;n->active_id=0;n->revision++;return 1;
}
int hd79_mount_stable(const hd79_mount_roster *r,hd79_mount_roster *n,const char *e,unsigned id,unsigned room,int stable,int present) {
 if(!hd79_mount_roster_valid(r)||!n||strcmp(r->epoch,e)||!id||id>r->count||!room)return -1;
 if(!stable||!present||r->entries[id-1].stabled)return 0;
 if(r->revision==UINT32_MAX)return -1;
 *n=*r;n->entries[id-1].stabled=1;n->entries[id-1].stable_room=room;
 if(n->active_id==id) { n->active_id=0; }
 n->revision++; return 1;
}
int hd79_mount_retrieve(const hd79_mount_roster *r,hd79_mount_roster *n,const char *e,unsigned id,unsigned room,int stable) {
 if(!hd79_mount_roster_valid(r)||!n||strcmp(r->epoch,e)||!id||id>r->count||!room)return -1;
 if(!stable||!r->entries[id-1].stabled||r->entries[id-1].stable_room!=room)return 0;
 if(r->revision==UINT32_MAX)return -1;
 *n=*r;n->entries[id-1].stabled=0;n->entries[id-1].stable_room=0;n->revision++;return 1;
}

int hd79_mount_award(const hd79_mount_roster *r,hd79_mount_roster *n,const char *e,int species,unsigned *id) {
 if(!r||!n||!e||!id||!hd79_mount_roster_valid(r)||strcmp(r->epoch,e))return -1;
 if(r->count>=HD79_MOUNT_MAX_OWNED || r->revision==UINT32_MAX)return 0;
 if(species<1 || species>6)return -1;
 *n=*r;*id=r->count+1;n->entries[r->count].id=*id;
 n->entries[r->count].species=species;n->entries[r->count].endurance=70;
 n->count++;n->revision++;return 1;
}
