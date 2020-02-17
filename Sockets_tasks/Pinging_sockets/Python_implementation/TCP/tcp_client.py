# Imports:
    # re -> Use regular expressions when finding the sequence number
    # time -> Allow introducing a delay so as not to overwhelm the server
    # The rest have been explained elsewhere!

import socket, sys, time, signal, re

# NOTE: Python "swallows" IPs and hostnames. It'll resolve hostnames automagically just by passign it to the socket!
# NOTE: Whatever happened to gethostbyname()...

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

    # Instantiate a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Define an exit handler
    def k_int_handler(foo, fuu):
        print("Quitting!")
        client_socket.close()
        exit(0)

    # Bind the avobe handler to CTRL + C
    signal.signal(signal.SIGINT, k_int_handler)

    # Try to connect to the server. Note the address we need to provide is a tuple
    # Containing the server's IP and Port unmber. If the server is not reachable
    # (i.e it's not running) connect() will throw an exception and exit. We could use
    # a tr/except block to catcch it and handle the situation to make it wait until it
    # finds a server for example but we believe it adds nothing to what we want to achieve!
    client_socket.connect((sys.argv[1], int(sys.argv[2])))

    while True:
        # We'll later see when using UDP at the transport layer how we also need to
        # specify a recipient address. This is not the case with TCP as it's a
        # connection oriented protocol!
        client_socket.send("Echo request".encode())

        # geat a message and decode it!
        in_msg = client_socket.recv(2048).decode()

        # If we cannot read any more data recv() will return an empty string ('')
        # That's our time to exit! Note how we need to provide two dummy parameters
        # for the exit handler...
        if in_msg == '':
            k_int_handler(None, None)
        
        # Find the incoming sequence number with a regular expression ('\d+') and
        # print an status message
        print("Echo reply # {}".format(re.findall(r'\d+', in_msg)[0]))

        # Stay idle for a second so that the server doesn't go nuts!
        time.sleep(1)

if __name__ == "__main__":
    main()
