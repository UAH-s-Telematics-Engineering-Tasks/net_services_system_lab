# All these imports have been explained elsewhere!
import socket, sys, re, time, signal

def main():
    # Check we received 2 parameters: The server's IP and port
    if len(sys.argv) != 3:
        print("Use: {} IP port".format(sys.argv[0]))
        exit(-1)

    # Validate the first argument is indeed an IP address through regular expressions. If we want to use symbolic names like 'localhost' we need to comment
    # it out or else the program will exit... The if clause takes advantage of the fact that match() returns None if it couldn't find any matches and an
    # object otherwise which is just what we need to know as None is treated in the same way as false when used as a condition
    if not re.match(r'(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)$', sys.argv[1]):
        print("The provided IP address is NOT valid!")
        exit(-1)

    # Instantiate a UDP socket
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Define an exit handler
    def k_int_handler(foo, fuu):
        print("Quitting!")
        client_sock.close()
        exit(0)

    # Bind the handler to CTRL + C
    signal.signal(signal.SIGINT, k_int_handler)

    while True:
        # Send a message to the server
        client_sock.sendto("Echo request".encode(), (sys.argv[1], int(sys.argv[2])))

        # Block until you get the reply
        in_msg, server_addr = client_sock.recvfrom(2048)

        # Decode it and find the sequence number with a regular expression ('\d+')
        # Print a pretty message with all that info
        print("Echo reply # {}".format(re.findall(r'\d+', in_msg.decode())[0]))

        # Stay idle for a second so that the server doesn't go nuts!
        time.sleep(1)

# If the script is run directly execute main()
if __name__ == "__main__":
    main()
