#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

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
void keyboard_int_handler(int);
void quit_error(char*);

volatile int continue_pinging = 1;

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Use: %s IP", argv[0])
        return -1;
    }
    // As seen in RFC 1700, page 8, IANA's Protocol Number for ICMP is 1
    int raw_sock = socket(AF_INET, SOCK_RAW, 1);

    struct sockaddr_in server_addr;

    // Refer to 'man raw.7' to see how sin_port should be set to 0 due to bugs in
    // the kernels network stack implementation!
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(0);
    if (!inet_aton(argv[1], &server_addr.s_addr))
        quit_error("The provided IP is NOT valid!\n");

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