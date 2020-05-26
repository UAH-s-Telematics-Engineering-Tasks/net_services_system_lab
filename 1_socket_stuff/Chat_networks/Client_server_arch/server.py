######################################################
#                   Imports                          #
# socket -> Let's us manage socket instances         #
# sys -> Grant access to the passed arguments        #
# select -> Let's us work concurrently with sockets  #
# os -> Let's us clear the screen when printing info #
######################################################

# NOTE: As these imports are always the same we'll just talk about them here so as not to bloat the document!

import socket, sys, select, os

##################################################################################################################
#                                  Closing sockets and the TIME_WAIT interval                                    #
# As seen in https://serverfault.com/questions/329845/how-to-forcibly-close-a-socket-in-time-wait and in         #
# RFC 793 (https://tools.ietf.org/html/rfc793), when closing a TCP socket it will remain "open" long             #
# enough to guarantee the FIN ACK segment has reached the opposite end. If we close the clients then             #
# the random port they've reserved will be held for some time. As clients are not binded to a specific port      #
# this will have no impact whatsoever when launching new clients, they'll just get a new port number and life    #
# will seamlessly go on. If we manually close the server however the port we had binded it to will continue      #
# to be used for TIME_WAIT seconds... We can check that by running netstat and looking at the top of the         #
# output. Lazy people like me would instead run netstat | head -n 20 and get away with it. We can configure      #
# this TIME_WAIT to be 0. I'm not sure whether that's done on form python on the socket or from the OS on the    #
# network manager... Anyway we should not forget it's there and that, even if we shut down our sockets correctly #
# we will have an inherent delay due to how TCP works... When we close every client gracefully and end up        #
# shutting the server down we won't experience this behaviour as the server is only left with the "listening"    #
# socket, there are NO connections open so there is no need to wait for them to receive the final message!       #
##################################################################################################################

##################################################################################################################
#                                          Allowing Outside Connections                                          #
# In order to allow connections from the outside we must bind the server to every interface or, at least the one #
# providing connectivity to the outside world. If we only bind to that "outwards" interface we won't be able to  #
# connect local clients... We can then choose to bind to '' instead of '127.0.0.1' which is interpreted as       #
# INADDR_ANY by Pyhton, that is, we'll bind the server to EVERY interface                                        #
##################################################################################################################

def main():
    if len(sys.argv) != 2:
        print("Use: {} <binding_port>".format(sys.argv[0]))
        exit(-1)

    # The readable_sources dictionary contains the different socket instances as values and some information identifying
    # them as the key. These keys will be derived from the first message sent by each client as soon as they connect.
    readable_sources = {'serving_sock': socket.socket(socket.AF_INET, socket.SOCK_STREAM)}

    # Bind the socket and get ready for incoming connections
    readable_sources['serving_sock'].bind(('127.0.0.1', int(sys.argv[1])))

    print("Listening for connections...")

    readable_sources['serving_sock'].listen(1)

    # These variables let us monitor images being sent through us so that we can
    # act accordingly
    img_passing = False
    passed_bytes = 0

    try:
        while True:
            for src in select.select(list(readable_sources.values()), [], [])[0]:

                # If we got a new client accept it and read its ID Tag. Note reading on a socket
                # not monitored by select() is not such a good idea as it may block our server
                # indefinitely but as we have implemented both the client and server we can
                # get away with this little "botch"
                if src == readable_sources['serving_sock']:
                    new_client = src.accept()[0]
                    readable_sources[new_client.recv(8148).decode()] = new_client

                # If the message came from a socket connected from a client
                else:
                    inc_msg = src.recv(8148)

                    # If there is no image traversing us at the moment we can safely decode the message.
                    # Otherwise we could be attempting to decode some invalid bytes and that would trigger
                    # an exception...
                    if not img_passing:

                        # If the peer socket's been closed close this end and remove it from the monitored list
                        if inc_msg.decode() == '':
                            src.close()

                            # As we are working with dictionaries so that we can print more meaningful information we need
                            # to jump thorugh some hoops to get the correct value to delete...
                            del readable_sources[list(readable_sources.keys())[list(readable_sources.values()).index(src)]]

                        # Our image sending protocol starts with an 'IMG_INCOMING!' message. It that's the case activate
                        # the "image mode" until the given number of bytes have passed
                        elif 'IMG_INCOMING!' in inc_msg.decode():
                            img_passing = True
                            passed_bytes = int(inc_msg.decode().split(';')[1])

                    # We are currently transmitting an image
                    else:

                        # Keep track of all the sent bytes
                        passed_bytes -= len(inc_msg)

                        # If we are done deactivate "image mode"
                        if passed_bytes == 0:
                            img_passing = False
                    
                    # As the data is of no interest to us we don't need to decode() it. We can just send it away
                    for c_sock in list(readable_sources.values())[1:]:
                            if c_sock != src:
                                c_sock.sendall(inc_msg)

            # As images can be large printing information on the screen at such a high rate makes the terminal flicker
            # so avoid printing any more information whilst an image is being sent
            if not img_passing:

                # Take advantage of the informative tags sent by the clients so that we can show meaningful info at the output!
                os.system("clear")
                print("Connected clients:")
                for client, c_sock in list(readable_sources.items())[1:]:
                    print("\t{} -> {}:{}".format(client, c_sock.getpeername()[0], c_sock.getpeername()[1]))

    # When we receive CTRL + C
    except KeyboardInterrupt:
        print("Quitting...")

        # Close every socket and quit!
        for sock in readable_sources.values():
            sock.close()
        exit(0)

if __name__ == '__main__':
    main()
