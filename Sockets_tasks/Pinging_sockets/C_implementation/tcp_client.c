#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>

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

    if(tcp_sock = socket(AF_INET, SOCK_STREAM, 0) == -1)
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
    serv_addr.sin_port = (in_port_t) htonl(atoi(argv[2]));

    // The call to inet_aton() already updates the contents of the struct!
    if(!inet_aton(argv[1], &serv_addr.sin_addr))
        quit_error("The provided IP address is NOT valid!\n");

    if(connect(tcp_sock, (struct sockaddr*) serv_addr, sizeof struct sockaddr_in))
        quit_error("Couldn't connect...\n");

    #if DBG
    printf("Connected to the server!\n");
    #endif

    while(continue_pinging) {

    }

}

void keyboard_int_handler(int dummy) {
    continue_pinging = 0;
    #if DBG
    printf("Quitting...\n");
    exit(0);
    #endif
}

void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}