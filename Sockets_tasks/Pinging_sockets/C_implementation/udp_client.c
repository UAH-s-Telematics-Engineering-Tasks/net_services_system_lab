#include <stdio.h>
#include <sys/socket.h>
// POSIX.1 doesn't require it... We can include it for portability!
// #include <sys/types.h>
// We'll use memset for clearing the address struct
#include <string.h>
// Byte order conversion a.k.a htonl()
#include <arpa/inet.h>

int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "Use: %s port\n", argv[0]);
        return -1;
    }
    #if DBG
    printf("Proceeding with port: %s\n", argv[1]);
    #endif

    /*
        AF_INET -> IPv4 socket
        SOCK_STREAM -> Connection Oriented Socket
        0 -> Use TCP as the transport protol. We have no other option though!
        Returns: (int) file descriptor to the newly created socket. Returns -1 on error
    */
    if((tcp_sock = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        fprintf(stderr, "Error creating the socket... Aborting!\n");
        return -1;
    }

    /*
        Let's build our address structure. As seen in 'man ip.7' we need to define a sockaddr_in struct for IPv4 sockets!
    */
    struct sockaddr_in sock_conf;
    // Zero out the entire struct
    memset(&sock_conf, 0, sizeof(struct sockaddr_in));

    // Set the socket family
    sock_conf.sin_family = AF_INET;

    // Set the port number from the passed argument
    sock_conf.sin_port = (in_port_t) htonl(atoi(argv[1]));

    // Bind to localhost!
    sock_conf.sin_addr.s_addr = hlon(INADDR_LOOPBACK);

    // // Set IP address number from the passed argument
    // if (!inet_aton(argv[1], &sock_conf.sin_addr) {
    //     fprintf(stderr, "The IP adress is NOT valid!\n");
    //     return -1;
    // }

    // Ready to bind!
    if (bind(tcp_sock, (struct sockaddr*) &sock_conf, sizeof(struct sockaddr_in))) {
        fprintf(stderr, "Error when binding...\n");
        return -1;
    }

    // Get it to listen. Add a queue of 5 connections
    if (listen(tcp_sock, 5)) {
        fprintf(stderr, "Error when trying to listen...\n");
        return -1;
    }

    


}