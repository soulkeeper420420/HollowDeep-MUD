/* Offline/private tests of the actual hd_deity.c command and persistence. */
#define _GNU_SOURCE
#include "mstruct.h"
#include "hollowdeep_staff.h"
#include "hd_deity.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <unistd.h>

static int actor_role=HD_ROLE_ADMIN, audit_allowed=1, audit_count=0, prints=0;
static char last_target[20],last_action[32];
int hd_staff_role(creature *p) { (void)p;return actor_role; }
int hd_staff_rank(int role) { return role==HD_ROLE_OWNER?3:role==HD_ROLE_ADMIN?2:role==HD_ROLE_MOD?1:role==HD_ROLE_PLAYER?0:-1; }
int hd_staff_saved_name(const char *input, char *output) {
 size_t i, n=strlen(input);
 if(n<3 || n>19) return 0;
 for(i=0;i<n;i++){
   if(!((input[i]>='a' && input[i]<='z')||(input[i]>='A' && input[i]<='Z'))) return 0;
   output[i]= i==0 ? (char)(input[i]>='a'? input[i]-32:input[i]) : (char)((input[i]>='A' && input[i]<='Z')?input[i]+32:input[i]);
 }
 output[n]=0;
 return !strcmp(output,"Hdnecro") || !strcmp(output,"Hdfighter") || !strcmp(output,"Hdtest");
}
int hd_staff_authorize_action(creature *p,int required,const char *action,const char *target,const char *value){
 (void)p;(void)required;(void)value;
 if(!audit_allowed) return 0;
 audit_count++;
 strcpy(last_target,target);strcpy(last_action,action);
 return 1;
}
void print(int fd, char *fmt, ...) { (void)fd; (void)fmt;prints++; }
creature *find_who(char *name){ (void)name;return NULL; }
int hd_staff_open_data(const char *name) {
 int fd;
 struct stat st;
 if(strcmp(name,"deities.db"))return -2;
 fd=open("deities.db",O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
 if(fd<0) return -1;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)|| st.st_size>32768||st.st_nlink!=1){close(fd);return -2;}
 return fd;
}
int hd_staff_write_data(const char *name,const char *data,unsigned long size){
 int fd;char tmp[]=".deity-tmp-XXXXXX";
 if(strcmp(name,"deities.db")||size>8192)return 0;
 fd=mkstemp(tmp);if(fd<0)return 0;
 if(write(fd,data,size)!=(ssize_t)size||fsync(fd)){close(fd);unlink(tmp);return 0;}
 close(fd);if(rename(tmp,"deities.db")){unlink(tmp);return 0;}return 1;
}
static void command(cmd *c,const char *line) { memset(c,0,sizeof(*c));strcpy(c->fullstr,line); }
static void run(creature *a,const char *line) {cmd c;command(&c,line);hd_dm_deity(a,&c);}
int main(void){
 creature dm={0};int before,fd;
 dm.type=PLAYER;dm.class=DM;dm.fd=3;strcpy(dm.name,"Realmkeeper");
 assert(hd_deity_get("Hdnecro")==0);
 run(&dm,"*deity list");
 run(&dm,"*deity Hdnecro");
 run(&dm,"*deity Hdnecro 3");
 assert(hd_deity_get("Hdnecro")==3 && hd_deity_assigned("Hdnecro"));
 assert(audit_count==1&&!strcmp(last_target,"Hdnecro")&&!strcmp(last_action,"powertry"));
 run(&dm,"*deity Hdfighter 16");
 assert(hd_deity_get("Hdfighter")==16);
 run(&dm,"*deity Hdnecro 7");assert(hd_deity_get("Hdnecro")==7);
 before=audit_count;
 run(&dm,"*deity Hdnecro -1");
 run(&dm,"*deity Hdnecro 17");
 run(&dm,"*deity Hdnecro 0x1");
 run(&dm,"*deity Hdnecro 1 trailing");
 run(&dm,"*deity Notexist 1");
 assert(audit_count==before&&hd_deity_get("Hdnecro")==7);
 actor_role=HD_ROLE_MOD;run(&dm,"*deity Hdnecro 0");assert(hd_deity_get("Hdnecro")==7);
 actor_role=HD_ROLE_ADMIN;dm.class=MAGE;run(&dm,"*deity Hdnecro 0");assert(hd_deity_get("Hdnecro")==7);
 dm.class=DM;audit_allowed=0;run(&dm,"*deity Hdnecro 0");assert(hd_deity_get("Hdnecro")==7);
 audit_allowed=1;run(&dm,"*deity Hdnecro 0");assert(hd_deity_get("Hdnecro")==0&&!hd_deity_assigned("Hdnecro"));
 assert(hd_deity_get("Hdfighter")==16);
 /* Malformed DB must not grant permissions OR be silently reset. */
 fd=open("deities.db",O_WRONLY|O_TRUNC);assert(fd>=0);assert(write(fd,"BAD\n",4)==4);close(fd);
 assert(hd_deity_get("Hdfighter")==-1);
 before=audit_count;run(&dm,"*deity Hdfighter 5");assert(audit_count==before+1);
 assert(hd_deity_get("Hdfighter")==-1);
 assert(prints>0);
 puts("DEITY: DM-only persisted ID map, admin audit, offline target, clear, invalid input/corrupt fail-closed PASS");
 return 0;
}
