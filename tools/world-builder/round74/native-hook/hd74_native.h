#ifndef HD74_NATIVE_H
#define HD74_NATIVE_H
/* Test-only native bridge. No automatic remort or player-file migration. */
struct creature;
struct cmd;
int hd74_parse_starting_stats(const char *text, int out[5]);
int hd74_progress(struct creature *player, struct cmd *command);
#endif
