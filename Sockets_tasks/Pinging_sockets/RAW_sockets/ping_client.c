#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

// TODO: Apply loops to packet generation
// NOTE: Reading from the raw_sock returns the IP Header too!!!!! Parse it out or prevent the socket from returning it all along...
// NOTE: Quitting with CTRL + C throws an exit code different than 0... Check out why!
// NOTE: Running the program requires sudo privileges. Otherwise port writes will just fail...

// Echo request anatomy -> https://en.wikipedia.org/wiki/Ping_(networking_utility)

/*
                                                            ECHO REQUEST STRCUTURE
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|           Type = 8            |               Code = 0              |                                  Checksum                                     |
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|                           Identifier                                |                                  Seq. Num                                     |
+-----------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  Payload                                                                            |
+-----------------------------------------------------------------------------------------------------------------------------------------------------+

Checksum -> Break the entire header into 16-bit chunks taking the checksum to have a value of 0. Add them together using one's complement addition and
            flip the result.
*/

int compute_checksum(int*, int);
void generate_icmp_msg(unsigned int*, int);
int little_to_big_endian(int);
int ones_complement_16_bit_sum(int, int, char);
int ones_complement_16_bit_sum_simple(int, int);
void keyboard_int_handler(int);
void quit_error(char*);

volatile int continue_pinging = 1;

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Use: %s IP\n", argv[0]);
        return -1;
    }
    // As seen in RFC 1700, page 8, IANA's Protocol Number for ICMP is 1. This is the protocol discriminator used in IP!
    int raw_sock = socket(AF_INET, SOCK_RAW, 1);

    struct sockaddr_in server_addr;

    // Refer to 'man raw.7' to see how sin_port should be set to 0 due to bugs in
    // the kernels network stack implementation!
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(0);
    if (!inet_aton(argv[1], &server_addr.sin_addr))
        quit_error("The provided IP is NOT valid!\n");

    unsigned int icmp_msg[6];
    generate_icmp_msg(icmp_msg, sizeof(icmp_msg));

    unsigned int serv_addr_size = sizeof server_addr;
    int curr_time, recv_bytes;
    int in_buff[60];
    while(continue_pinging) {
        printf("Sent bytes: %ld", sendto(raw_sock, icmp_msg, sizeof(icmp_msg), 0, (struct sockaddr*) &server_addr, sizeof(server_addr)));
        recv_bytes = recvfrom(raw_sock, in_buff, sizeof(in_buff), 0, (struct sockaddr*) &server_addr, &serv_addr_size);
        printf("\tReceived %d bytes from %s\n", recv_bytes, inet_ntoa(server_addr.sin_addr));
        curr_time = time(NULL);
        while(time(NULL) - curr_time < 1);
    }
    close(raw_sock);
    return 0;
}

int compute_checksum(int* arr, int n_elms) {
    int checksum = 0;
    for (int i = 0; i < n_elms; i++)
        for (int mask_shift = 1; mask_shift >= 0; mask_shift--)
            checksum = ones_complement_16_bit_sum_simple((arr[i] & (0xFFFF << 16 * mask_shift)) >> 16 * mask_shift, checksum);
    return (~checksum) & 0xFFFF;
}

void generate_icmp_msg(unsigned int* msg, int size) {
    char type = 0x08, code = 0x00;
    int checksum = 0x0000, id = 0x0005, seq_num = 0x000A;

    msg[0] = type << 24 | code << 16 | checksum;
    msg[1] = id << 16 | seq_num;
    msg[2] = 'S' << 24 | 'a' << 16 | 'i' << 8 | 'b';
    msg[3] = 'a' << 24 | ' ' << 16 | 'S' << 8 | 'a';
    msg[4] = 'm' << 24 | 'u' << 16 | 'r' << 8 | 'a';
    msg[5] = 'i' << 24 | '!' << 16 | 'P' << 8 | 'c';

    // Adjust to the network's endianness!
    msg[0] = little_to_big_endian(msg[0] | compute_checksum(msg, 6));
    msg[1] = little_to_big_endian(msg[1]);
    msg[2] = little_to_big_endian(msg[2]);
    msg[3] = little_to_big_endian(msg[3]);
    msg[4] = little_to_big_endian(msg[4]);
    msg[5] = little_to_big_endian(msg[5]);
}

int little_to_big_endian(int n) {
    int little_end_bytes[4];
    for (int i = 0; i < 4; i++)
        little_end_bytes[i] = (n & (0xFF << i * 8)) >> i * 8;

    return little_end_bytes[0] << 24 | little_end_bytes[1] << 16 | little_end_bytes[2] << 8 | little_end_bytes[3];
}

int ones_complement_16_bit_sum(int x, int y, char recirculate) {
    int aux_result = 0, carry = 0, aux_operand = y;
    // If we are just recirculating the carry take into account the offset we apply to the second operand so that
    // we don't have to rewrite the condition within the for loop...
    if (!recirculate)
        aux_operand = 1;

    for (int k = 0; k < 16; k++) {
            if (((x & 0x1 << k) >> k) != ((aux_operand & 0x1 << k) >> k))
                aux_result |= (carry ^ 0x1) << k;
            else {
                aux_result |= carry << k;
                if (x & 0x1 << k)
                    carry = 1;
                else
                    carry = 0;
            }
        }
    if (carry && recirculate)
        aux_result = ones_complement_16_bit_sum(aux_result, 1, 0);

    return aux_result & 0xFFFF;
}

int ones_complement_16_bit_sum_simple(int x, int y) {
    int aux_result = (x & 0xFFFF) + (y & 0xFFFF);

    // If we had an overflow recirculate the carry!
    // Max result = 2 * (2^16 - 1) = 2^17 - 2 -> In this case we only need to recirculate the carry once too!
    if (aux_result >= 0X10000)
        aux_result++;

    return aux_result & 0xFFFF;
}

void keyboard_int_handler(int dummy) {
    continue_pinging = 0;
    #if INTCLOSE
        printf("Quitting...\n");
        exit(0);
    #endif
}

void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}