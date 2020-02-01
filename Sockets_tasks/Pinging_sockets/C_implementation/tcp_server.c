#include <stdio.h>
#include <sys/socket.h>
// POSIX.1 doesn't require it... We can include it for portability!
// #include <sys/types.h>
// We'll use memset for clearing the address struct
#include <string.h>
// Byte order conversion a.k.a htonl()
#include <arpa/inet.h>
// R/W
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>

#define BUFF_SIZE 65
#define QUEUE_LEN 5

volatile int loop_flag = 1;

void keyboard_int_handler(int);
void quit_error(char*);

int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "Use: %s port\n", argv[0]);
        return -1;
    }

    #if DBG
    printf("Proceeding with port: %s\n", argv[1]);
    #endif

    signal(SIGINT, keyboard_int_handler);

     int seq_number = 0, tcp_sock, client_fd, read_bytes = 0;
     char buffer[BUFF_SIZE] = {0}, backup_buffer[BUFF_SIZE] = {0};

    /*
        AF_INET -> IPv4 socket
        SOCK_STREAM -> Connection Oriented Socket
        0 -> Use TCP as the transport protol. We have no other option though!
        Returns: (int) file descriptor to the newly created socket. Returns -1 on error
    */
    if((tcp_sock = socket(AF_INET, SOCK_STREAM, 0)) == -1)
        quit_error("Error creating the socket... Aborting!\n");

    #if DBG
    printf("Created the socket!\n");
    #endif

    /*
        Let's build our address structure. As seen in 'man ip.7' we need to define a sockaddr_in struct for IPv4 sockets!
    */
    struct sockaddr_in sock_conf, client_sock;

    // Zero out the entire struct
    memset(&sock_conf, 0, sizeof(struct sockaddr_in));
    memset(&client_sock, 0, sizeof(struct sockaddr_in));

    // Set the socket family
    sock_conf.sin_family = AF_INET;

    // Set the port number from the passed argument
    sock_conf.sin_port = (in_port_t) htonl(atoi(argv[1]));

    // Bind to localhost!
    sock_conf.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    #if DBG
    printf("Server address: %s\n", inet_ntoa(sock_conf.sin_addr));
    #endif

    // Ready to bind!
    if (bind(tcp_sock, (struct sockaddr*) &sock_conf, sizeof(struct sockaddr_in)))
        quit_error("Error when binding...\n");

    #if DBG
    printf("Binded the socket!\n");
    #endif

    // Get it to listen. Add a queue of 5 connections
    if (listen(tcp_sock, QUEUE_LEN))
        quit_error("Error when trying to listen...\n");

    #if DBG
    printf("Hush! We are listening!\n");
    #endif

    /*
        Listening sockets are blocing by default in the sense that calls to accept() involving this passive socket will block the caller until a connection is present. This implies we'll be blocked if the queue is empty and we'll extract queued connections otherwise! We just need to run an infinite loop getting those clientes but before that we need to define a structure for getting the client's info! Note that an empty constan defaults to a non-zero value as found in C's standard; that's why for (;;) is an infinite loop but we prefer the more classic and simpler while (1);
    */

    // We need to declare an int containing the size of the sockets or else we won't be able to get the desired address with the & operator...
    long int client_sock_size = sizeof(struct sockaddr_in);

    if ((client_fd = accept(tcp_sock, (struct sockaddr*) &client_sock, (socklen_t *) &client_sock_size)) == -1)
            quit_error("Error when accepting the connection...\n");

    #if DBG
    printf("Accepted a connection! Loop time!\n");
    #endif

    while(loop_flag) {
        if ((read_bytes = read(client_fd, buffer, BUFF_SIZE)) != -1 && read_bytes < 15)
            while(read_bytes < 15) {
                read_bytes += read(client_fd, backup_buffer, BUFF_SIZE);
                strcat(buffer, backup_buffer);
            }
        else
            quit_error("Error when reading data...\n");

        seq_number += 1;

        // We don't really care about buffer boundaries. We are crafting the message!
        sprintf(backup_buffer, "Echo reply # %d", seq_number);

        if (!strcmp("Echo request", buffer)) {
            printf("Received an echo request from: %s:%d\n", inet_ntoa(client_sock.sin_addr), ntohl(client_sock.sin_port));
            write(client_fd, backup_buffer, sizeof(backup_buffer));
        }
        else {
            printf("Received a weird message from: %s:%d\n", inet_ntoa(client_sock.sin_addr), ntohl(client_sock.sin_port));
        }
    }
    close(client_fd);
    close(tcp_sock);
    return 0;
}

void keyboard_int_handler(int dummy) {
    loop_flag = 0;
    #if DBG
    printf("Quitting...\n");
    exit(0);
    #endif
}

void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}