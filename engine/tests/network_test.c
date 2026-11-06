/* Socket-free tests of the actual engine input compatibility helper. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mtype.h"
#include "hollowdeep_net.h"

static int assertions;

static void check(int condition, const char *description)
{
    assertions++;
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", description);
        exit(1);
    }
}

static size_t feed(int fd, const unsigned char *bytes, size_t length,
                   unsigned char *output)
{
    size_t i, size = 0;
    int decoded;
    for (i = 0; i < length; i++) {
        decoded = hd_net_feed(fd, bytes[i]);
        if (decoded >= 0) output[size++] = (unsigned char)decoded;
    }
    return size;
}

static void sequence(int fd, const unsigned char *input, size_t length,
                     const unsigned char *expected, size_t expected_length,
                     const char *description)
{
    unsigned char output[512];
    size_t size = feed(fd, input, length, output);
    check(size == expected_length && !memcmp(output, expected, size), description);
}

int main(void)
{
    int option, command, fd = 7;
    unsigned char negotiation[4], output[4];
    const unsigned char subnegotiation[] = {
        255, 250, 24, 0, 'M', 'U', 'D', 'L', 'E', 'T',
        255, 255, 'X', '\r', '\n', 255, 240, 'A', '\r', '\n'
    };
    const unsigned char protocol_between_line_end[] = {'\r', 255, 253, 86, '\n', 'x'};
    const unsigned char escaped_iac[] = {255, 255, 'x'};
    const unsigned char literal_iac[] = {255, 'x'};

    hd_net_reset(fd);
    sequence(fd, (const unsigned char *)"Smokehero\r\n", 11,
             (const unsigned char *)"Smokehero\n", 10, "CRLF is one line");
    check(hd_net_feed(fd, '\r') == '\n', "split CR produces Enter immediately");
    check(hd_net_feed(fd, '\n') == -1, "later LF is consumed across reads");
    check(hd_net_feed(fd, 'p') == 'p', "password byte after split CRLF survives");
    check(hd_net_feed(fd, '\r') == '\n', "CR before split NUL produces Enter");
    check(hd_net_feed(fd, 0) == -1, "later NUL after CR is consumed");
    check(hd_net_feed(fd, '\n') == '\n', "bare LF remains Enter");
    sequence(fd, (const unsigned char *)"\r\r\n", 3,
             (const unsigned char *)"\n\n", 2, "consecutive CRs remain two Enters");
    check(hd_net_feed(fd, 8) == 8, "backspace reaches original input editor");
    sequence(fd, (const unsigned char *)"say hello\n", 10,
             (const unsigned char *)"say hello\n", 10, "plain commands unchanged");

    /* Every option byte, including printable IDs, must stay out of credentials. */
    for (command = 251; command <= 254; command++) {
        for (option = 0; option <= 255; option++) {
            hd_net_reset(fd);
            negotiation[0] = 255;
            negotiation[1] = (unsigned char)command;
            negotiation[2] = (unsigned char)option;
            negotiation[3] = 'N';
            check(feed(fd, negotiation, sizeof(negotiation), output) == 1 && output[0] == 'N',
                  "IAC WILL/WONT/DO/DONT option never leaks into text");
        }
    }
    hd_net_reset(fd);
    check(hd_net_feed(fd, 255) == -1, "fragmented IAC consumed");
    check(hd_net_feed(fd, 253) == -1, "fragmented DO consumed");
    check(hd_net_feed(fd, 86) == -1, "fragmented printable option consumed");
    check(hd_net_feed(fd, 'S') == 'S', "name after fragmented negotiation intact");
    sequence(fd, subnegotiation, sizeof(subnegotiation),
             (const unsigned char *)"A\n", 2, "TTYPE subnegotiation payload and escaped IAC consumed");
    sequence(fd, escaped_iac, sizeof(escaped_iac), literal_iac, sizeof(literal_iac),
             "escaped IAC data survives");
    sequence(fd, protocol_between_line_end, sizeof(protocol_between_line_end),
             (const unsigned char *)"\nx", 2, "negotiation does not split CRLF pairing");

    hd_net_reset(8);
    check(hd_net_feed(fd, '\r') == '\n', "first client has pending CR");
    check(hd_net_feed(8, '\n') == '\n', "second client LF is independent");
    check(hd_net_feed(fd, '\n') == -1, "first client keeps its own CR state");
    check(hd_net_feed(fd, 255) == -1, "first client starts negotiation");
    check(hd_net_feed(8, 'S') == 'S', "second client text independent of negotiation");
    hd_net_reset(fd);
    check(hd_net_feed(fd, 'N') == 'N', "reset clears incomplete negotiation on reused fd");
    check(hd_net_feed(fd, '\r') == '\n', "pending CR before disconnect");
    hd_net_reset(fd);
    check(hd_net_feed(fd, '\n') == '\n', "reset clears pending CR on reused fd");
    check(hd_net_feed(-1, 'x') == -1, "negative descriptor rejected");
    check(hd_net_feed(PMAX, 'x') == -1, "out-of-bounds descriptor rejected");
    hd_net_reset(-1);
    hd_net_reset(PMAX);
    check(hd_net_feed(fd, 'y') == 'y', "invalid resets do not disturb valid client");
    printf("PASS: %d native input normalization assertions\n", assertions);
    return 0;
}
