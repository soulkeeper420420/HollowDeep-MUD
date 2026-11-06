/*
 * Hollowdeep input compatibility for the original Mordor 3.00 engine.
 * Keep original engine copyright and distribution terms with this source.
 *
 * TCP reads do not preserve lines or Telnet commands. State belongs to a
 * connection, never to the on-disk player/world structures. Call reset when
 * accepting and closing a descriptor, including incomplete login sessions.
 */
#include "mtype.h"
#include "hollowdeep_net.h"

enum hd_telnet_state {
    HD_DATA, HD_IAC, HD_OPTION, HD_SUBNEGOTIATION, HD_SUBNEGOTIATION_IAC
};

struct hd_input_state {
    unsigned char telnet;
    unsigned char after_cr;
};

static struct hd_input_state inputs[PMAX];

void hd_net_reset(int fd)
{
    if (fd < 0 || fd >= PMAX) return;
    inputs[fd].telnet = HD_DATA;
    inputs[fd].after_cr = 0;
}

int hd_net_feed(int fd, unsigned char byte)
{
    struct hd_input_state *state;
    if (fd < 0 || fd >= PMAX) return -1;
    state = &inputs[fd];

    switch (state->telnet) {
    case HD_DATA:
        if (byte == 255) {
            state->telnet = HD_IAC;
            return -1;
        }
        break;
    case HD_IAC:
        if (byte >= 251 && byte <= 254) state->telnet = HD_OPTION;
        else if (byte == 250) state->telnet = HD_SUBNEGOTIATION;
        else state->telnet = HD_DATA;
        if (byte == 255) break; /* Escaped literal IAC is ordinary data. */
        return -1;
    case HD_OPTION:
        state->telnet = HD_DATA;
        return -1;
    case HD_SUBNEGOTIATION:
        if (byte == 255) state->telnet = HD_SUBNEGOTIATION_IAC;
        return -1;
    case HD_SUBNEGOTIATION_IAC:
        state->telnet = byte == 240 ? HD_DATA : HD_SUBNEGOTIATION;
        return -1;
    default:
        hd_net_reset(fd);
        return -1;
    }

    /* Treat CR LF and CR NUL as one Enter, even across separate read() calls.
     * Telnet commands are removed first and do not interrupt this pairing. */
    if (state->after_cr) {
        state->after_cr = 0;
        if (byte == '\n' || byte == 0) return -1;
    }
    if (byte == '\r') {
        state->after_cr = 1;
        return '\n';
    }
    return byte;
}
