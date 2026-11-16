/* Round 73I: private-test exact-PID ledger protocol. NO reward grants. */
#ifndef HD_LEDGER_BRIDGE_H
#define HD_LEDGER_BRIDGE_H
#include <sys/types.h>
#include "hd_guard_proof.h"
#define HD_LEDGER_DENIED (-1)
#define HD_LEDGER_OK 0
#define HD_LEDGER_READY 1
#define HD_LEDGER_PENDING 2
int hd_ledger_begin(const char *sock, uid_t server_uid, const hd_guard_proof *proof);
int hd_ledger_kill(const char *sock, uid_t server_uid, const hd_guard_proof *proof, unsigned index);
int hd_ledger_claim(const char *sock, uid_t server_uid, const hd_guard_proof *proof);
#endif
