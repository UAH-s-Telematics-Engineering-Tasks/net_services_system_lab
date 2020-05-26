#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
#include <netdb.h>

#define BUFF_SIZE 64

void keyboard_int_handler(int);
void quit_error(char*);

volatile int continue_pinging = 1;
volatile int udp_sock;

int main(int argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "Use: %s  IP | hostname port\n", argv[0]);
        return -1;
    }

    #ifdef DBG
        printf("Proceeding with: %s:%s\n", argv[1], argv[2]);
    #endif

    signal(SIGINT, keyboard_int_handler);

    if ((udp_sock = socket(AF_INET, SOCK_DGRAM, 0)) == -1)
        quit_error("Couldn't create the socket...\n");

    #ifdef DBG
        printf("Created the client socket!\n");
    #endif

    struct sockaddr_in server_addr;
    unsigned int serv_addr_size = sizeof server_addr;

    // Configure the struct  "pointing to" the server we are ging to talk to
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(atoi(argv[2]));

    // Resolve the provided hostname through gethostbyname()
    server_addr.sin_addr = *((struct in_addr*) gethostbyname(argv[1])->h_addr_list[0]);

    /*
        Note inet_ntoa() has a statically allocated buffer "inside" and thus subsequent calls to inet_ntoa() overwrite said buffer.
        We would need to malloc() space or define a char array otherwise...
    */
    #ifdef DBG
        printf("Server is @:\n\tIP: %s\tPORT: %d\n", inet_ntoa(server_addr.sin_addr), ntohs(server_addr.sin_port));
    #endif

    char in_buffer[BUFF_SIZE] = {0};
    int curr_time = 0, recv_bytes = 0, last_seq_number = -1;
    while (continue_pinging) {
        /*
            Send the echo request to the server we have configured through the server_addr struct. If there is an error
            (write() returns -1) exit the while loop.
        */
        if(sendto(udp_sock, "Echo request", sizeof "Echo request", 0, (struct sockaddr*) &server_addr, sizeof server_addr) == -1)
            break;

        /*
            Receive the reply. The call to recvfrom() is blocking in the sense we will be stuck here until we receive something.
            In case of reaching the EOF recvfrom() will return 0. In case or error it'll return -1.
        */
        if((recv_bytes = recvfrom(udp_sock, in_buffer, BUFF_SIZE, 0, (struct sockaddr*) &server_addr, &serv_addr_size)) <= 0)
            break;

        // Look for the sequence number in the incoming reply
        if(last_seq_number < atoi(strpbrk(in_buffer, "0123456789"))) {
            last_seq_number = atoi(strpbrk(in_buffer, "0123456789"));
            printf("Got reply: %s\n", in_buffer);
        }

        // Introduce a 1 second delay
        curr_time = time(NULL);
        while(time(NULL) - curr_time < 2);
    }
    #ifdef DBG
        printf("Tearing down...\n");
    #endif
    close(udp_sock);
    return 0;
}

void keyboard_int_handler(int dummy) {
    continue_pinging = 0;
    #if INTCLOSE
        close(udp_sock);
        printf("Quitting...\n");
        exit(0);
    #endif
}

void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}