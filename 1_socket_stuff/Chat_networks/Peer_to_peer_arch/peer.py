import socket, sys, select

################################################################
#               SIGNALLING MESSAGE FORMATS                     #
# peer_info (see line 95) -> "peer_username;peer_IP;peer_port" #
################################################################

def main():
    if len(sys.argv) != 4:
        print("Use: {} <server_IP> <server_port> <username>".format(sys.argv[0]))
        exit(-1)
    elif sys.argv[3] == 'introduction_sock' or sys.argv[3] == 'entry_sock' or sys.argv[3] == 'keybrd':
        print("Invalid username!")
        exit(-1)

    # CLI Stuff
    prompt = 'Type something --> '
    clear_prompt = "\x1B[1G" + "\x1B[2K"
    clear_input = "\x1B[1F" + "\x1B[2K"

    # We'll use this list to check whether a key is associated with a peer or it is related to a "special" socket.
    # This'll let us condense code when printing peer_sockets' keys as we'll see later on as well as decide who
    # to send messages to!
    special_sockets = ['keybrd', 'introduction_sock', 'entry_sock']

    # This dictionary will hold every monitored socket plus the keyboard:
        # 'keyboard' -> The associated value is the keyboard's file descriptor
        # 'introduction_sock' -> UDP socket used to introduce ourselves to the net and get info regarding active peers
                               # We'll also use it when disconnecting to inform the server so that it forgets about us
        # 'entry_sock' -> TCP socket used for accepting new peers

    # New entries will use the peer's username as the dictionaries key and the value will be the corresponding socket instance
    peer_sockets = {'keybrd': sys.stdin,
                    'introduction_sock': socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                    'entry_sock': socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    }

    # Binding to port number 0 will use any available port. The kernel will be smart enough to assign one.
    # Begin listening for new peers afterwards
    peer_sockets['entry_sock'].bind(('127.0.0.1', 0))
    peer_sockets['entry_sock'].listen(1)

    # The getsockname() method lets us get the IP and PORT of a given socket. Remember we are not using a user supplied port...
    print("We are listening for peers @ {}:{}".format(peer_sockets['entry_sock'].getsockname()[0], peer_sockets['entry_sock'].getsockname()[1]))

    # Tell the server we are up so that it takes note and sends back info about already existing peers
    peer_sockets['introduction_sock'].sendto(("I'm up!;" + sys.argv[3] + ';' + str(peer_sockets['entry_sock'].getsockname()[1])).encode(),
                                             (sys.argv[1], int(sys.argv[2])))

    print("We have introduced ourselves to the central server!\nTime to connect to the peers!")

    try:
        while True:

            # Write the prompt and flush it, remember we don't have a trailing '\n'
            print(prompt, end = '', flush = True)
            ready_socks = select.select(list(peer_sockets.values()), [], [])[0]
            for src in ready_socks:

                # If the user typed a message
                if src == sys.stdin:

                    # Read it
                    in_data = sys.stdin.readline().rstrip()

                    # If the user want's to know who he/she is connected to...
                    if in_data == 'get_status':
                        print(clear_input + "Connected peers:")

                        # Print the associated peer_sockets' keys, i.e, the usernames
                        for peer in peer_sockets:

                            # As dicitonaries don't have to be ordered we'll check the name we print doesn't belong to either the
                            # keyboard, the introduction UDP socket or the binded TCP one. This is why we defined the special_sockets
                            # list at the beginning.
                            if peer not in special_sockets:
                                print("\t" + peer)

                    # If it's a regular message
                    else:

                        # Build it by appending your own username
                        out_msg = sys.argv[3] + " -> " + in_data
                        print(clear_input + out_msg)

                        # Send the message only to peers!
                        for peer, sock in peer_sockets.items():
                            if peer not in special_sockets:
                                sock.sendall(out_msg.encode())

                # If there is a message coming to the UDP socket it must be info about a peer
                elif src == peer_sockets['introduction_sock']:

                    # Parse the incoming message
                    peer_info = src.recv(8148).decode().split(';')

                    # Add an entry in the peer_sockets dictionary
                    peer_sockets[peer_info[0]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Tell the user we have received info about a new client
                    print(clear_prompt + "Connecting to peer {} @ {}:{}".format(peer_info[0], peer_info[1], peer_info[2]))

                    # Connect to said client
                    peer_sockets[peer_info[0]].connect((peer_info[1], int(peer_info[2])))

                    # Send our username to the new peer right away. He/she will be waiting for it!
                    peer_sockets[peer_info[0]].sendall(sys.argv[3].encode())

                # If a new peer is connecting to us
                elif src == peer_sockets['entry_sock']:

                    # Accept it
                    new_sock, new_addr = src.accept()

                    # Get it's username. Reading here is not as dangerous as it could be because all peers are implemented in the
                    # same way!
                    peer_username = new_sock.recv(8148).decode()

                    # Tell the user a new peer is connecting to us
                    print(clear_prompt + "Got new peer {} @ {}:{}".format(peer_username, new_addr[0], new_addr[1]))

                    # Add the new peer to our dictionary
                    peer_sockets[peer_username] = new_sock

                # If the message came to an already connected socket
                else:

                    # Decode it
                    inc_msg = src.recv(8148).decode()

                    # If we get an empty string (i.e EOF) it means the other end has closed the socket
                    if inc_msg == '':

                        # Get the socket's index
                        socket_index = list(peer_sockets.keys())[list(peer_sockets.values()).index(src)]

                        # Tell the user a peer has disconnected
                        print(clear_prompt + "Disconecting from peer {} @ {}:{}".format(socket_index, src.getpeername()[0], src.getpeername()[1]))

                        # Close it
                        src.close()

                        # And delete it
                        del peer_sockets[socket_index]

                    # Otherwise just print the message
                    else:
                        print(clear_prompt + inc_msg)

    # If we get a CTRL + C signal
    except KeyboardInterrupt:
        print("Quitting...")

        # Tell the server we are leaving
        peer_sockets['introduction_sock'].sendto(("Bye!;" + sys.argv[3]).encode(), (sys.argv[1], int(sys.argv[2])))

        # Close all the open sockets, including the UDP and binded TCP ones
        for peer in list(peer_sockets.values())[1:]:
            peer.close()

        # And quit
        exit(0)

if __name__ == "__main__":
    main()