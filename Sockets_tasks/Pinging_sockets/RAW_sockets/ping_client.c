#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

// TODO: Change the endiannes to BIG ENDIAN! Take into account it happens at the BYTE level... Call htons() and mask away!
// TODO: Fix the checksum computation...
// NOTE: Reading from the raw_sock returns the IP Header too!!!!! Parse it out or prevent the socket from returning it all along...
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
int ones_complement_16_bit_sum(int, int, char);
void print_binary_16_bit_n(int);
void keyboard_int_handler(int);
void quit_error(char*);

volatile int continue_pinging = 1;

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Use: %s IP", argv[0]);
        return -1;
    }
    // As seen in RFC 1700, page 8, IANA's Protocol Number for ICMP is 1
    int raw_sock = socket(AF_INET, SOCK_RAW, 1);

    struct sockaddr_in server_addr;

    // Refer to 'man raw.7' to see how sin_port should be set to 0 due to bugs in
    // the kernels network stack implementation!
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(0);
    if (!inet_aton(argv[1], &server_addr.sin_addr))
        quit_error("The provided IP is NOT valid!\n");

    // Checksum without payload: 0xFFF5
    // int icmp_msg[2] = {0x0000 << 16 | 0x00 << 8 | 0x08, 0x0001 << 16 | 0x0001};
    int icmp_msg[4] = {0xDE27 << 16 | 0x00 << 8 | 0x08, 0x0001 << 16 | 0x0001, 0x50 << 24, 0x6F6C6261};
    // icmp_msg[0] = (icmp_msg[0] & 0xFFFF) | compute_checksum(icmp_msg, sizeof(icmp_msg) / sizeof(icmp_msg[0])) << 16;
    // icmp_msg[0] |= (compute_checksum(icmp_msg, sizeof(icmp_msg) / sizeof(icmp_msg[0])) & 0xFFFF) << 16;

    printf("ICMP Message Header:\n");
    for (int i = 0; i < sizeof(icmp_msg) / sizeof(icmp_msg[0]); i++)
        for (int k = 0; k < sizeof(icmp_msg[0]) * 8 / 16; k++) {
            printf("\t");
            print_binary_16_bit_n(icmp_msg[i] >> 16 * k);
        }

    unsigned int serv_addr_size = sizeof server_addr;
    int curr_time;
    int in_buff[10];
    while(continue_pinging) {
        printf("Sent bytes: %ld", sendto(raw_sock, icmp_msg, sizeof(icmp_msg), 0, (struct sockaddr*) &server_addr, sizeof(server_addr)));
        printf("\tReceived bytes: %ld\n", recvfrom(raw_sock, in_buff, 10 * 4, 0, (struct sockaddr*) &server_addr, &serv_addr_size));
        curr_time = time(NULL);
        while(time(NULL) - curr_time < 1);
    }
    close(raw_sock);
    return 0;
}

int compute_checksum(int* arr, int n_elms) {
    int checksum = 0;
    for (int i = 0; i < n_elms; i++)
        for (int mask_shift = 0; mask_shift < 2; mask_shift++)
            checksum = ones_complement_16_bit_sum(arr[i] & (0xFFFF << 16 * mask_shift), checksum, 1);
    return (~checksum) & 0xFFFF;
}

int ones_complement_16_bit_sum(int x, int y, char recirculate) {
    // n = 16 as that's the boundry between the numbers. We prefer to show the logic to obtain that result
    int aux_result = 0, carry = 0, n = sizeof(x) * (8 / 2), aux_operand = y;
    // If we are just recirculating the carry take into account the offset we apply to the second operand so that
    // we don't have to rewrite the condition within the for loop...
    if (!recirculate)
        aux_operand = 1 << n;

    for (int k = 0; k < n; k++) {
            if (((x & 0x1 << k) >> k) != ((aux_operand & 0x1 << k + n) >> k + n))
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

void print_binary_16_bit_n(int n) {
    for (int i = 0; i < 16; i++) {
        if (n & 1 << i)
            printf("1");
        else
            printf("0");
    }
    printf("\n");
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