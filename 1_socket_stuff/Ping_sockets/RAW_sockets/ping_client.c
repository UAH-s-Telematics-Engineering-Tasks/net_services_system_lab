#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

// NOTE: Reading from the raw_sock returns the IP Header too!!!!! Parse it out or prevent the socket from returning it all along if you want to get info like the incoming payload
    // and the like. I believe you cannot prevent the IP header from being returned though...

// NOTE: Quitting with CTRL + C throws an exit code different than 0... Check out why!

// NOTE: Running the program requires sudo privileges. Otherwise port writes will just fail as we are using RAW sockets. Investigate linux capabilities to allow the program to use RAW
    // sockets without requeiring root privileges

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

void generate_icmp_msg(unsigned int*, int);
int compute_checksum(int*, int);
int ones_complement_16_bit_sum_simple(int, int);
int ones_complement_16_bit_sum(int, int, char);
int little_to_big_endian(int);
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

    // This function will modify icmp_msg[] as we are passing it by reference
    generate_icmp_msg(icmp_msg, sizeof(icmp_msg));

    // We need to define a variable containing the structs size as C doesn't like us using &sizeof(serv_addr)...
    unsigned int serv_addr_size = sizeof(server_addr);
    int curr_time, recv_bytes;

    // Buffer holding the incoming message
    int in_buff[60];
    while(continue_pinging) {
        printf("Sent bytes: %ld", sendto(raw_sock, icmp_msg, sizeof(icmp_msg), 0, (struct sockaddr*) &server_addr, sizeof(server_addr)));
        printf("\tReceived %ld bytes from %s\n", recvfrom(raw_sock, in_buff, sizeof(in_buff), 0, (struct sockaddr*) &server_addr, &serv_addr_size), inet_ntoa(server_addr.sin_addr));
        sleep(1);
    }
    close(raw_sock);
    return 0;
}

// Generate the entire ICMP header and store it in the buffer pointed to by msg. The codes and the like are explained at the beginning of the source file!
// We are then configuring a custom payload for testing purposes: "Saiba Samurai!Pc" The real ping client includes the timestamp to compute Round Trip Times
// and avoid having to store the time it sent each packet! Compliant ping "servers" need to include the payload as is in the replies
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

    for (int i = 1; i < size / sizeof(msg[0]); i++)
        msg[i] = little_to_big_endian(msg[i]);
}

// Function to compute the 16-bit one's complement sum of the inputs as the message is longer than 32-bits...
// We are just dividing the message in 16-bit chunks and adding them up. Remember the checksum is taken to be
// 0 when computing it!
int compute_checksum(int* arr, int n_elms) {
    int checksum = 0;
    for (int i = 0; i < n_elms; i++)
        for (int mask_shift = 1; mask_shift >= 0; mask_shift--)
            checksum = ones_complement_16_bit_sum_simple((arr[i] & (0xFFFF << 16 * mask_shift)) >> 16 * mask_shift, checksum);
    return (~checksum) & 0xFFFF;
}

// Function implementing a 16-bit one's complement addition taking advantage of bit-level masks!
int ones_complement_16_bit_sum_simple(int x, int y) {
    int aux_result = (x & 0xFFFF) + (y & 0xFFFF);

    // If we had an overflow recirculate the carry!
    // Max result = 2 * (2^16 - 1) = 2^17 - 2 -> In this case we only need to recirculate the carry once too!
    if (aux_result >= 0X10000)
        aux_result++;

    return aux_result & 0xFFFF;
}

// Does the same as the above but in a more explicit, bit-level way so that it is clearer how the one's complement
// sum "works". Even though the function is recursive it will NOT go out of control as if we recirculate the carry
// in the worst case scenario it will NOT provoke a second carry. That is:
// 0xFFFF + 0xFFFF will provoke a carry and yield 0xFFFE. When recirculating we'll get the final result 0xFFFF
// without a second carry recirculation! The above assumes a 16-bit one's complent sum!
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

// Function used to convert from my PC's little endian CPU (it's made by Intel) to the network's big endian
// byte order. We could have maybe used htons() or htonl() for a more portable solution but we wanted to try
// our hand at writing it ourselves. If using a big endian PC adjust the function above accordingly so as to
// avoid making the little -> big endian conversion!
int little_to_big_endian(int n) {
    int little_end_bytes[4];
    for (int i = 0; i < 4; i++)
        little_end_bytes[i] = (n & (0xFF << i * 8)) >> i * 8;

    return little_end_bytes[0] << 24 | little_end_bytes[1] << 16 | little_end_bytes[2] << 8 | little_end_bytes[3];
}

// Keyboard interrupt (CTRL + C) handler
void keyboard_int_handler(int dummy) {
    continue_pinging = 0;
    #if INTCLOSE
        printf("Quitting...\n");
        exit(0);
    #endif
}

// Helper function for printing an error message and exiting
void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}