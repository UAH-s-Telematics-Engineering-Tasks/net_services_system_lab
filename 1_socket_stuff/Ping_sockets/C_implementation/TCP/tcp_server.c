// Output functions like printf() and the like
#include <stdio.h>

// Include everything sockect related
#include <sys/socket.h>

// POSIX.1 doesn't require these types to be explicitly included
// We could include them for portability though
// #include <sys/types.h>

// We'll use memset for clearing the address struct
#include <string.h>

// Byte order conversion so that we adapt our little endian computer
// to a big endian network. This is done by functions like htonl()
#include <arpa/inet.h>

// R/W functions that act on file descriptors
#include <unistd.h>

// CRTL + C handler for a cleaner exit
#include <signal.h>

// System calls like exit()
#include <stdlib.h>

/*
 * These constants define the length of the buffer we are reading into
 * and the number of incoming connections we can simultaneously keep
 * in the input queue respectively
 */
#define BUFF_SIZE 65
#define QUEUE_LEN 5

// This flag is altered by the CTRL + C handler to trigger the program's exit
volatile int loop_flag = 1;

// Auxiliary function prototypes. The definitions can be found after main()
void keyboard_int_handler(int);
void quit_error(char*);

int main(int argc, char** argv) {
    // Check we only received 1 parameter: the port to bind the server to
    if (argc != 2) {
        fprintf(stderr, "Use: %s port\n", argv[0]);
        return -1;
    }

    // We have used compile time flags to alter the programs vervosity!
    #if DBG
    printf("Proceeding with port: %s\n", argv[1]);
    #endif

    /*
        Attach the keyboard_int_handler() function to the CTRL + C (SIGINT) signal
        That is, CTRL + C willbe handled by keyboard_int_handler()
    */
    signal(SIGINT, keyboard_int_handler);

    /*
        Forward declaration of used variables.
        The buffers are used to handle the incoming messages
    */
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
        client_sock will contain the client's data when we accept a connection as we'll see later on
    */
    struct sockaddr_in sock_conf, client_sock;

    /*
        Zero out the entire struct
        These are not strictly necessary as we'll initialize every field within the structs
        It's a common practice though and it can potentially avoid looking for "ghost" errors...
    */
    memset(&sock_conf, 0, sizeof(struct sockaddr_in));
    memset(&client_sock, 0, sizeof(struct sockaddr_in));

    // Set the socket family. AF_INET == IPv4
    sock_conf.sin_family = AF_INET;

    /*
        Set the port number from the passed argument converted to network byte order
        We are using htonl() because atoi() returns an int (not a short) data type
        We are then casting it to the type shown in man 1p.7 (a.k.a in_port_t) to be
        as correct as possible even though it's not strictly necessary. We could also
        use, as seen, htons() as port numbers are represented by 16-bit numbers only!
        This would truncate a higher value to a correct one or so we pressume, we would
        need to take a look at the implementation... Anyhow, the main idea is we need to
        be aware of the data endianness when writing data that's ultimtely going to travel
        through the network. We tried both versions out of curiosity and both seem to be
        working perfectly fine
    */
    #if DBG
    int port = atoi(argv[1]);
    sock_conf.sin_port = htons(port);
    #else
    sock_conf.sin_port = (in_port_t) htonl(atoi(argv[1]));
    #endif

    /*
        Listen on the loopback interface "lo". Take care of setting the correct endiannes!
    */
    sock_conf.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    #if DBG
    printf("Server address: %s:%d\n", inet_ntoa(sock_conf.sin_addr), ntohs(sock_conf.sin_port));
    #endif

    /*
        Ready to bind using the data we have configured in the sock_conf struct.
        In order to comply with the function prototype seen in man bind.2 we need
        to cast the pointer to the sock_conf address to a pointer to a sockaddr struct.
        The sole purpose of casting to sockaddr is avoiding compiler warnings as seen
        in man bind.2
    */
    if (bind(tcp_sock, (struct sockaddr*) &sock_conf, sizeof(struct sockaddr_in)))
        quit_error("Error when binding...\n");

    #if DBG
    printf("Binded the socket!\n");
    #endif

    // Start listening for connections on the socket
    if (listen(tcp_sock, QUEUE_LEN))
        quit_error("Error when trying to listen...\n");

    #if DBG
    printf("Hush! We are listening!\n");
    #endif

    /*
        Calling accept will block the caller (main() in this case) until we have a connection
        to extract from the queue. The program will continue running after accepting said connection.

        Listening sockets are blocking by default in the sense that calls to accept()
        involving this passive socket will block the caller until a connection is present.
        This implies we'll be blocked if the queue is empty and we'll extract queued
        connections otherwise! We just need to run an infinite loop getting those clientes
        but before that we need to define a structure for getting the client's info! Note
        that an empty constant defaults to a non-zero value as found in C's standard; that's
        why for (;;) is an infinite loop but we prefer the more classic and simpler while (1);
    */

    // We need to declare an int containing the size of the sockets or else we won't be able to get the desired address with the & operator...
    long int client_sock_size = sizeof(struct sockaddr_in);

    /*
        We are passing the client_sock struct so that it is filled up with info describing the new client
        We also need to cast some types here (like socklen_t) to comply with the prototypes... This one
        can be found at man accept.2
    */
    if ((client_fd = accept(tcp_sock, (struct sockaddr*) &client_sock, (socklen_t *) &client_sock_size)) == -1)
            quit_error("Error when accepting the connection...\n");

    #if DBG
    printf("Connected to: %s:%d. Loop time!\n", inet_ntoa(client_sock.sin_addr), ntohs(client_sock.sin_port));
    #endif

    while(loop_flag) {
        // If we read 0 bytes then assume the client has closed the connection and set the exit flag appropriately
        if ((read_bytes = read(client_fd, buffer, BUFF_SIZE)) > 0)
            while(read_bytes < sizeof("Echo request")) {
                read_bytes += read(client_fd, backup_buffer, BUFF_SIZE);
                strcat(buffer, backup_buffer);
            }
        else
            loop_flag = 0;

        #if DBG
        printf("Received %d bytes! Message: %s\n", read_bytes, buffer);
        #endif

        // Increment the sequence number with every new message
        seq_number += 1;

        /*
            Craft the messages into the backup_buffer. As we have the entire message at "buffer"
            we can reuse the backup one so that we don't need to define a third one to store
            our response message
        */
        sprintf(backup_buffer, "Echo reply # %d", seq_number);

        if (!strcmp("Echo request", buffer)) {
            #if DBG
            printf("Received an echo request!\n");
            #endif
            /*
                Send the reply to the client. If we cannot write to the socket quit. Write returns -1 on error as seen
                on man write.2
            */
            if(write(client_fd, backup_buffer, sizeof(backup_buffer)) == -1)
                loop_flag = 0;
        }
        #if DBG
        /*
            The following has been mainly used for debugging purposes. inet_ntoa() translates an incoming
            IP address to a string that's easier to handle. ntohs converts network byte order to the one
            used by the host. In our case the conversion is from big endian to little endian
        */
        else
            printf("Received a weird message from: %s:%d\n", inet_ntoa(client_sock.sin_addr), ntohs(client_sock.sin_port));
        #endif
    }
    #if DBG
    printf("Client disconnected!\n");
    #endif
    // Close both sockets and exit
    close(client_fd);
    close(tcp_sock);
    return 0;
}

/*
    CTRL + C handler
    We need to define a dummy variable as these handlers are passed a parameter
    the thing is we won't be using it for anything. We still need to avoid compiler
    warnings... This just sets the appropriate flag to exit the main loop.
*/
void keyboard_int_handler(int dummy) {
    loop_flag = 0;
    #if INTCLOSE
    printf("Quitting...\n");
    exit(0);
    #endif
}

/*
    Helper function for exiting in case of error and printing a message in the process.
*/
void quit_error(char* err_msg) {
    fprintf(stderr, "%s", err_msg);
    exit(-1);
}