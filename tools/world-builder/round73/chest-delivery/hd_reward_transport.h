/* Round 73J: trusted-PID test-only immutable manifest/receipt transport. */
#ifndef HD_REWARD_TRANSPORT_H
#define HD_REWARD_TRANSPORT_H
#include "hd_native_reward.h"
#include "hd_ledger_bridge.h"
#define HD_TRANSPORT_DENIED (-1)
#define HD_TRANSPORT_MANIFEST 0
#define HD_TRANSPORT_ALREADY 1
int hd_reward_fetch(const char *socket_path, uid_t trusted_uid,
                    const hd_guard_proof *proof, hd_native_reward *reward);
int hd_reward_ack(const char *socket_path, uid_t trusted_uid,
                  const hd_guard_proof *proof, const hd_native_reward *reward);
#endif
