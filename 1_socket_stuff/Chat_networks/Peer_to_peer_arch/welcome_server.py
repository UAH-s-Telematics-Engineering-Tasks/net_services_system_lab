import socket, select, sys, os

##################################################################
#                   SIGNALLING MESSAGE FORMATS                   #
# Welcome Message Format -> "I'm up!;username;entry_socket_port" #
# Peer Address Format    -> "IP:Port"                            #
# Goodbye Message Format -> "Bye!;username"                      #
##################################################################

def main():
    if len(sys.argv) != 2:
        print("Use: {} <binding_port>".format(sys.argv[0]))
        exit(-1)

    # We're using UDP for sending and receiving messages
    welcome_soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Begin listening for new and departing peers
    welcome_soket.bind(('127.0.0.1', int(sys.argv[1])))

    # This dictionary contains the usernames as keys and a string of
    # the form 'IP:PORT' as values. These are the IP and PORT of
    # a peer's welcome socket, i.e, the one it accepts connections on
    active_peers = {}

    print("Waiting for new peers...")

    try:
        while True:
            # Using select here is just overkill but we want to be consistent...
            for src in select.select([welcome_soket], [], [])[0]:

                # This is the only possible source anyway... Checking it improves readability though!
                if src == welcome_soket:

                    # We'll need the sender's IP. Note ther is no use for the port number as it
                    # belongs to the UDP socket and we are only concerned with the TCP socket
                    # accepting connections. That's the one the peer will let us know about!
                    msg, source = src.recvfrom(8148)

                    # If the peer is introducing itslef
                    if "I'm up!" in msg.decode():

                        # Send info pertaining already connected peers back
                        for peer, cnx_point in active_peers.items():
                            src.sendto((peer + ';' + cnx_point).encode(), source)

                        # Then add an entry for this new peer in our dictionary
                        active_peers[msg.decode().split(';')[1]] = source[0] + ';' + msg.decode().split(';')[2]

                    # If the peer is disconnecting
                    elif "Bye!" in msg.decode():

                        # Just delete the associated entry in our dictionary
                        del active_peers[msg.decode().split(';')[1]]

            # Clear the terminal's screen
            os.system("clear")
            print("Live peers:")

            # Take advantage of the meaningful keys we are using to show information on the current network status
            for peer, cnx_point in active_peers.items():
                print("\t{} -> {}:{}".format(peer, cnx_point.split(';')[0], cnx_point.split(';')[1]))

    # If we receive CTRL + C
    except KeyboardInterrupt:
        print("Quitting...")

        # Close the socket and quit but don't tell the peers. The P2P network must function independently of this server!
        welcome_soket.close()
        exit(0)

if __name__ == "__main__":
    main()