/*
    We'll only stop ourselves on the aspects we haven't touched on in previous
    source files so as not to drag things on unnecessarily
*/

#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <errno.h>

/*
    Let's us get the current time through time() so as not
    to overwhelm the server with too many messages by
    introducing a delay
*/
#include <time.h>

/*
    Lets us make a DNS resolution through gethostbyname()
*/
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
    // Create a TCP socket
    if((tcp_sock = socket(AF_INET, SOCK_STREAM, 0)) == -1)
        quit_error("Error creating the socket... Good bye!\n");

    #if DBG
    printf("Created the client socket!\n");
    #endif

    /*
        No need to bind the socket, we can get a random port number!
    */

    /*
        We'll configure serv_addr so that it contains the necessary information
        to connect to the desired server
    */
    struct sockaddr_in serv_addr;

    memset(&serv_addr, 0, sizeof serv_addr);

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(atoi(argv[2]));
    /*
        Function gethostbyname() accepts either an IP address or a hostname as an input in the
        form of a string (that is, a char*) and returns the address of a hostent structure. We
        can find an array of pointers to structs containing information relative to the obtained IP
        within this hostent. The address of this first pointer is stored in the h_addr_list memeber,
        so gethostbyname()->h_addr_list is the pointer to a pointer to a struct containing the end
        host's IP address. We can get the pointer to said struct by accessing:
        gethostbyname->h_addr_list[0] so the only thing there's left for us to do is dereference this
        pointer. Before doing so we'll cast it to a pointer to an structure of type in_addr
        (remember we cannot cast to a struct type in C (i.e. we cannot do (struct in_addr foo)))
        which is the one our serv_addr.sin_addr member expects. After applying the dereference operator
        * we have all we need! We should point out that if we provide an IP instead of a hostname to
        gethostyname() it'll just copy that address to this struct we are looking for so we don't need
        to check we are in fact passing a host name to the function. That's quite handy!

        All this info can be found in man gethostbyname
    */
    serv_addr.sin_addr = *((struct in_addr*) gethostbyname(argv[1])->h_addr_list[0]);

    // Previous code before using gethostbyname()
    // // The call to inet_aton() already updates the contents of the struct!
    // if(!inet_aton(argv[1], &serv_addr.sin_addr))
    //     quit_error("The provided IP address is NOT valid!\n");

    #if DBG
    printf("Server address: %s:%d\n", inet_ntoa(serv_addr.sin_addr), ntohs(serv_addr.sin_port));
    #endif

    // Connect to the configured server socket
    if(connect(tcp_sock, (struct sockaddr*) &serv_addr, sizeof(struct sockaddr_in)))
        quit_error("Couldn't connect...\n");

    #if DBG
    printf("Connected to the server!\n");
    #endif

    // Forward declaration of used variables
    char in_buffer[BUFF_SIZE] = {0}, aux_buffer[BUFF_SIZE] = {0};

    int curr_time = 0, recv_bytes = 0, last_seq_number = 0;
    while(continue_pinging) {
        // Send the ping request
        if(write(tcp_sock, "Echo request", sizeof "Echo request") == -1)
            continue_pinging = 0;

        /*
            If we are filling up our buffer we could have more message to read
            We'll do so while we continue filling it up. If we read 0 bytes
            we've reached the End Of File and will then close the connection
        */
        if((recv_bytes = read(tcp_sock, in_buffer, BUFF_SIZE)) == BUFF_SIZE)
            while(read(tcp_sock, aux_buffer, BUFF_SIZE) == BUFF_SIZE)
                strcat(in_buffer, aux_buffer);
        else if (!recv_bytes)
            continue_pinging = 0;

        /*
            Look for the sequence number within the incoming message to check whether
            we got a new message. Function strpbrk() returns a pointer to the first character
            in in_buffer appearing in "0123456789" (i.e. a pointer to the first digit in in_buffer)
            As we know our server appends the sequence number to the responses, that is, it adds
            it at the end we can take advantage of NULL ('\0') terminated strings in C so that we
            only read the number if we begin reading from the position returned by strpbrk() 
        */
        if(last_seq_number < atoi(strpbrk(in_buffer, "0123456789"))) {
            last_seq_number = atoi(strpbrk(in_buffer, "0123456789"));
            printf("Got reply: %s\n", in_buffer);
        }

        /*
            We didn't know there was a simpler sleep() function so we read the time (in seconds)
            with the time() function and waited for a second doing nothing so as not to overwhelm
            the server with too many requests
        */
        curr_time = time(NULL);
        while(time(NULL) - curr_time < 1);
    }
    #ifdef DBG
    printf("Closing the connection!\n");
    #endif
    // Exit and clean up the socket
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