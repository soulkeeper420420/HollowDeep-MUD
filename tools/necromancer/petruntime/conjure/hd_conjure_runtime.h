#ifndef HD_CONJURE_RUNTIME_H
#define HD_CONJURE_RUNTIME_H

int hd_cj_command(creature *, cmd *);
int hd_cj_is_pet(creature *);
int hd_cj_death(creature *);
int hd_cj_assist(creature *, creature *);

void hd_cj_login(creature *);
void hd_cj_logout(creature *);
void hd_cj_follow(creature *, room *);
void hd_cj_tick(void);
void hd_cj_checkpoint_all(void);
void hd_cj_unload(room *);
void hd_cj_status(creature *);

#endif
