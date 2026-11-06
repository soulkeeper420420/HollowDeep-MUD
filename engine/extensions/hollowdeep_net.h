/* Incremental client input normalization; no serialized Mordor fields change. */
#ifndef HOLLOWDEEP_NET_H
#define HOLLOWDEEP_NET_H

void hd_net_reset(int fd);
/* Returns -1 for consumed protocol bytes, or a normalized data byte (0..255). */
int hd_net_feed(int fd, unsigned char byte);

#endif
