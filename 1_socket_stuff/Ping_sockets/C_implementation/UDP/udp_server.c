/*
    We'll only comment on the things we haven't gone through on previous source files
    so as not to drag things on unnecessarily
*/

#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>

#define BUFF_SIZE 65
#define CLIENT_SIZE 10

/*
    This struct let's us concurrently handle many users keeping separate sequence numbers.
    Each new client is associated with once struct which keeps track of its current sequence
    number. We have hardcoded an array holding up to CLIENT_SIZE elements but we could
    theoretically implement this mechanismi with dynamica memory procedures (i.e malloc())
    to handle as many clients as our hardware is capable of
*/
struct client_echo {
    unsigned int ip_addr;
    unsigned int port;
    int seq_number;
};

volatile int loop_flag = 1;

/*
    Declaring the soocket's file desriptor here let's us close it from the
    CTRL + C handler in an easier way!
*/
volatile int udp_sock;

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

    /*
        Create a UDP (SOCK_DGRAM) socket!
    */
    if((udp_sock = socket(AF_INET, SOCK_DGRAM, 0)) == -1)
        quit_error("Error when creating the socket...\n");

    #if DBG
        printf("The socket is up!\n");
    #endif

    struct sockaddr_in sock_conf, client_data;
    unsigned int addr_struct_size = sizeof(client_data);

    // Not really necessary as we are initializing everything...
    // memset(&sock_conf, 0, sizeof(struct sockaddr_in));

    sock_conf.sin_family = AF_INET;
    sock_conf.sin_port = htons(atoi(argv[1]));
    sock_conf.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    #if DBG
        printf("Socket settings\n\tIP: %s\tPORT: %d\n", inet_ntoa(sock_conf.sin_addr), ntohs(sock_conf.sin_port));
    #endif

    if(bind(udp_sock, (struct sockaddr*) &sock_conf, sizeof(struct sockaddr_in)))
        quit_error("Error when binding Mr. Socket...\n");

    #if DBG
        printf("Binded the socket correctly!\n");
        printf("Let's get some data!\n");
    #endif

    char in_buffer[BUFF_SIZE] = {0}, backup_buffer[BUFF_SIZE] = {0};
    int read_bytes = 0;
    struct client_echo client_id[CLIENT_SIZE];

    // Initialize the client_id array containing info iding each client
    for (int i = 0; i < CLIENT_SIZE; i++) {
        client_id[i].ip_addr = -1;
        client_id[i].port = -1;
        client_id[i].seq_number = 0;
    }

    int k = 0;

    // Begin serving clients!
    while(loop_flag) {
        /*
            Read the info into in_buffer. Continue reading if we didn't get a full request and join the message int in_buffer
            by calling strcat() for concatenating both the main and backup buffers. It is utterly important to record the
            client's info into client_data as we need it to find out this clien't sequence number...
        */
        if((read_bytes = recvfrom(udp_sock, in_buffer, BUFF_SIZE, 0, (struct sockaddr*) &client_data, &addr_struct_size)) > 0)
            while(read_bytes < sizeof("Echo request")) {
                read_bytes += recvfrom(udp_sock, in_buffer, BUFF_SIZE, 0, (struct sockaddr*) &client_data, &addr_struct_size);
                strcat(in_buffer, backup_buffer);
            }
        else
            loop_flag = 0;

        for (k = 0; k < CLIENT_SIZE; k++) {
            // If it's not a new client increment the sequence number and stop reading the array
            if(client_id[k].ip_addr == client_data.sin_addr.s_addr && client_id[k].port == client_data.sin_port) {
                client_id[k].seq_number += 1;
                break;
            }
            /*
                If it's a new client initialize a new struct
                That's why initializing the array was really important!
            */
            else if (client_id[k].ip_addr == -1) {
                client_id[k].ip_addr = client_data.sin_addr.s_addr;
                client_id[k].port = client_data.sin_port;
                break;
            }
        }

        #if DBG
            printf("Message from: %s:%d\n\tContent: %s\n", inet_ntoa(client_data.sin_addr), ntohs(client_data.sin_port), in_buffer);
        #endif
        // Build the echo reply by reusing the backup buffer. Recycling is a must!
        sprintf(backup_buffer, "Echo reply # %d", client_id[k].seq_number);
        
        /*
            Send the reply to the client. If we cannot write to the socket quit. Write returns -1 on error as seen
            on man write.2
        */
        if(!strcmp(in_buffer, "Echo request")) {
            if(sendto(udp_sock, backup_buffer, BUFF_SIZE, 0, (struct sockaddr*) &client_data, addr_struct_size) == -1)
                loop_flag = 0;
        }
        #if DBG
        else
            printf("Got a weird message...\n");
        #endif
    }
    #if DBG
        printf("Client disconnected or no more data to read!\n");
    #endif
    close(udp_sock);
    return 0;
}

void keyboard_int_handler(int dummy) {
    loop_flag = 0;
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