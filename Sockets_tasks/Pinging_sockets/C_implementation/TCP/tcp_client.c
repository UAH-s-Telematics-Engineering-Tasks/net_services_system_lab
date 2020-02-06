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

int main(int argc, char** argv) {
    if(argc != 3) {
        fprintf(stderr, "Use: %s  IP | hostname port\n", argv[0]);
        return -1;
    }

    #if DBG
    printf("Proceeding with: %s:%s\n", argv[1], argv[2]);
    #endif

    signal(SIGINT, keyboard_int_handler);

    int tcp_sock = 0;
    if((tcp_sock = socket(AF_INET, SOCK_STREAM, 0)) == -1)
        quit_error("Error creating the socket... Good bye!\n");

    #if DBG
    printf("Created the client socket!\n");
    #endif

    /*
        No need to bind the socket, we can get a random port number!
    */

    struct sockaddr_in serv_addr;

    memset(&serv_addr, 0, sizeof serv_addr);

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(atoi(argv[2]));
    serv_addr.sin_addr = *((struct in_addr*) gethostbyname(argv[1])->h_addr_list[0]);

    // // The call to inet_aton() already updates the contents of the struct!
    // if(!inet_aton(argv[1], &serv_addr.sin_addr))
    //     quit_error("The provided IP address is NOT valid!\n");

    #if DBG
    printf("Server address: %s:%d\n", inet_ntoa(serv_addr.sin_addr), ntohs(serv_addr.sin_port));
    #endif

    if(connect(tcp_sock, (struct sockaddr*) &serv_addr, sizeof(struct sockaddr_in)))
        quit_error("Couldn't connect...\n");
        // printf("Error when connecting: %s\n", strerror(errno));

    #if DBG
    printf("Connected to the server!\n");
    #endif

    char in_buffer[BUFF_SIZE] = {0}, aux_buffer[BUFF_SIZE] = {0};

    int curr_time = 0, recv_bytes = 0, last_seq_number = 0;
    while(continue_pinging) {
        if(write(tcp_sock, "Echo request", sizeof "Echo request") == -1)
            continue_pinging = 0;

        if((recv_bytes = read(tcp_sock, in_buffer, BUFF_SIZE)) == BUFF_SIZE)
            while(read(tcp_sock, aux_buffer, BUFF_SIZE) == BUFF_SIZE)
                strcat(in_buffer, aux_buffer);
        else if (!recv_bytes)
            continue_pinging = 0;

        // Let's find the sequence number and check if we got a new reply...
        if(last_seq_number < atoi(strpbrk(in_buffer, "0123456789"))) {
            last_seq_number = atoi(strpbrk(in_buffer, "0123456789"));
            printf("Got reply: %s\n", in_buffer);
        }

        curr_time = time(NULL);
        while(time(NULL) - curr_time < 1);
    }
    #ifdef DBG
    printf("Closing the connection!\n");
    #endif
    close(tcp_sock);
    return 0;
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