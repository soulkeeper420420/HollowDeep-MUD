/* Exercise prepared Mordor accept_input() through real pipes, without sockets. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include "mstruct.h"
#include "mextern.h"
#include "hollowdeep_net.h"

/* Use the exact anonymous structure declaration from the original engine. */
__typeof__(Ply) Ply;

static int assertions;
static int reader, writer;
static iobuf buffer;

static void check(int condition, const char *description)
{
    assertions++;
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", description);
        exit(1);
    }
}

static void reset_input(void)
{
    memset(&buffer, 0, sizeof(buffer));
    buffer.intrpt = 1;
    Ply[reader].io = &buffer;
    hd_net_reset(reader);
}

static void send_input(const unsigned char *bytes, size_t length)
{
    if (write(writer, bytes, length) != (ssize_t)length) {
        perror("write test pipe");
        exit(1);
    }
    accept_input(reader);
}

static void send_text(const char *text)
{
    send_input((const unsigned char *)text, strlen(text));
}

static int contains(const char *expected)
{
    size_t length = strlen(expected);
    return buffer.itail == 0 && buffer.ihead == (int)length &&
           !memcmp(buffer.input, expected, length);
}

int main(void)
{
    int descriptors[2], flags;
    const unsigned char nul = 0;
    const unsigned char iac = 255, do_option = 253, mccp = 86;
    const unsigned char echo_reply[] = {255, 253, 1};
    const unsigned char subnegotiation[] = {255, 250, 24, 0, 'M', 'U', 'D', 'L', 'E', 'T', '\r', '\n'};
    const unsigned char end_subnegotiation[] = {255, 240};

    check(pipe(descriptors) == 0, "create local test pipe");
    reader = descriptors[0];
    writer = descriptors[1];
    check(reader >= 0 && reader < PMAX, "pipe descriptor fits original player table");
    reset_input();
    send_text("Smokehero\r");
    check(buffer.commands == 1 && contains("Smokehero\n"), "name CR queues exactly one complete line");
    check(buffer.intrpt & 1, "completed CR allows output prompt");
    send_text("\n");
    check(buffer.commands == 1 && contains("Smokehero\n"), "LF in a separate read cannot queue empty password");
    check(buffer.intrpt & 1, "consumed LF preserves output prompt");
    send_text("Reply\r\n");
    check(buffer.commands == 2 && contains("Smokehero\nReply\n"), "subsequent reply stays one complete line");

    reset_input();
    send_text("name\r");
    send_input(&nul, 1);
    check(buffer.commands == 1 && contains("name\n"), "CR NUL across reads is one complete line");
    check(buffer.intrpt & 1, "CR NUL leaves prompt output enabled");

    reset_input();
    send_input(&iac, 1);
    check(buffer.ihead == 0 && (buffer.intrpt & 1), "fragmented IAC does not alter buffer or prompt");
    send_input(&do_option, 1);
    check(buffer.ihead == 0 && (buffer.intrpt & 1), "fragmented DO does not suppress prompt");
    send_input(&mccp, 1);
    check(buffer.ihead == 0 && buffer.commands == 0 && (buffer.intrpt & 1), "printable Telnet option never prefixes name");
    send_text("Smokehero\r\n");
    check(buffer.commands == 1 && contains("Smokehero\n"), "name after Telnet negotiation remains intact");

    reset_input();
    send_input(subnegotiation, sizeof(subnegotiation));
    check(buffer.ihead == 0 && buffer.commands == 0 && (buffer.intrpt & 1), "TTYPE text and embedded line endings do not enter input");
    send_input(end_subnegotiation, sizeof(end_subnegotiation));
    send_text("Smokehero\r\n");
    check(buffer.commands == 1 && contains("Smokehero\n"), "name follows fragmented subnegotiation intact");

    reset_input();
    send_text("partial");
    check(!(buffer.intrpt & 1) && buffer.commands == 0, "partial typed line preserves original prompt behavior");
    send_input(echo_reply, sizeof(echo_reply));
    check(!(buffer.intrpt & 1) && contains("partial"), "protocol-only read preserves partial-line prompt state");
    send_text("\r");
    send_input(echo_reply, sizeof(echo_reply));
    send_text("\n");
    check(buffer.commands == 1 && contains("partial\n") && (buffer.intrpt & 1), "negotiation between CR LF does not create another line");

    reset_input();
    send_text("a%b\bC\n");
    check(buffer.commands == 1 && contains("a%%C\n"), "original percent escaping and backspace still work");
    flags = fcntl(reader, F_GETFL);
    check(flags >= 0 && fcntl(reader, F_SETFL, flags | O_NONBLOCK) == 0, "set test reader nonblocking");
    accept_input(reader);
    check(buffer.commands == 1 && contains("a%%C\n"), "EAGAIN does not disconnect or damage buffered command");
    check(buffer.intrpt & 1, "EAGAIN preserves prompt state");
    close(writer);
    accept_input(reader);
    check(buffer.commands == -1, "actual EOF still marks disconnected");
    close(reader);
    hd_net_reset(reader);
    printf("PASS: %d original accept_input integration assertions\n", assertions);
    return 0;
}
