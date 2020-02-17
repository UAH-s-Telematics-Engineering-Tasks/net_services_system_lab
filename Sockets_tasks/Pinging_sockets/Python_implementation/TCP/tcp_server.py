# Imports:
    # socket -> Facilities for socket creation
    # threading -> Utilities to emply threads for parallel programming
    # sys -> Allow access to the arguments passed from the shell
    # signal -> Lets us use handlers for signals like CTRL + C

import socket, threading, sys, signal

# Global variables accessed by several threads.
# simul_users keeps track of concurrent users
# thread_kill is a "flag" variable used to make
# every running thread terminate so that we can
# cleanly exit the program!
simul_users = 0
thread_kill = False

# This function will be launched to handle every new client connecting to us
def client_connection (c_socket, addr):
    # Decalre simul_users as global so that we can change it from within the function
    global simul_users

    # Increment the number of simultaneous users
    simul_users += 1

    # Initialize a sequence number for the current user/connection
    seq_number = 0
    print("Thread started for: {}:{}".format(addr[0], addr[1]))

    # Continue executing until we try to exit and have to terminate every thread
    while not thread_kill:
        # The socket is blocking by default so we will stay here until we receive a message
        # recv() returns the read message as a python bytes object which we need to
        # decode if we want to use it as a string later on...
        # 2048 specifies the maximum data to receive at once, i.e, the buffer size
        message = c_socket.recv(2048).decode()

        # If we cannot read any more data recv() will return an empty string ('')
        # That's our time to disconnect the client! We just need to disconnect the socket
        # and update the number of simultaneous users. Returning from this function will
        # implicitly kill the thread that was running it so we don't need to be all
        # that concerced about housekeeping...
        if message == '':
            print('Client {}:{} disconnected...'.format(addr[0], addr[1]))
            simul_users -= 1
            c_socket.close()
            return
        elif message == "Echo request":
            # If we got an echo reply increment the sequence number and send the message.
            # Note how we have to encode() it to convert the string into a bytes object
            # which is what sockets know how to handle. We are also capturing every
            # exception that can be triggered by writing to the client socket and
            # disconnecting it in case we experienced an error. This is done, as shown
            # with the help of a try/except block
            seq_number += 1
            try:
                c_socket.send("Echo reply # {}".format(seq_number).encode())
            except:
                print("Socket closed!")
                simul_users -= 1
                c_socket.close()
                return

def main():
    # Check we were only passed a parameter, the port number to bind to
    if len(sys.argv) != 2:
        print("Use: {} port".format(sys.argv[0]))
        exit(-1)

    # Define a list containing the several thread objects we'll be creating
    threads = []

    # Instantiate a socket with the following characteristics:
        # socket.AF_INET -> IPv4
        # socket.SOCK_STREAM -> TCP @ the transport layer
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # This function is here so that it 'sees' server_socket to be able to close it!
    def k_int_handler(foo, fuu):
        # We need to define thread_kill as global to be able to modify it like before!
        global thread_kill

        # Set the flag to force every thread to exit
        thread_kill = True
        print("Shutting down!")

        # Wait until all threads do in fact finish
        for thread in threads:
            thread.join()

        # Close the socket and call it a day
        server_socket.close()
        exit(0)

    # Bind the above handler to the SIGINT (CTRL + C) signal
    signal.signal(signal.SIGINT, k_int_handler)

    # Bind the socket to the localhost ('127.0.0.1') interface on the provided port
    # We don't have to deal with endiannes conversion like before!
    # Use server_socket.bind('', int(sys.argv[1])) to allow outside connections!
    # '' == sock.INADDR_ANY -> Bind to every interface!
    server_socket.bind(('127.0.0.1', int(sys.argv[1])))

    # Begin accepting connections. Calling listen() will block us until we get a
    # new connection. The passed parameter tells the socket to only keep one client
    # in a queue and reject all the other connections. As we are using threads to handle
    # the clients we'll see how this will only happen if we get a load of simultaneous
    # connections, we expect this queue to be empty most of the time!
    server_socket.listen(1)

    print("Ready for connections!")

    while True:
        # Note this info will only be updated on screen when we get a new connection.
        # We should include it in several parts of the client handler (client_connection)
        # but we didn't want to bloat the code with print()s...
        print("Number of active connections: %d" % (simul_users))

         # Wait here until you get a new connection! Upon acceptance, accept() will
         # return a connected socket to the client DIFFERENT than the one we accepted
         # the connection on as well as his/her IP and port number
        connection_socket, client_addr = server_socket.accept()

        # Create a new thread and add it to our threads list. We need to tell the
        # constructor that the thread will run the client_connection() function and
        # we will be passing it parameters connection_socket and client_addr when it's
        # started. Note these parameters are passed inside a tuple
        threads.append(threading.Thread(target = client_connection, args = (connection_socket, client_addr)))

        # Print some interesting info
        print("# of created threads: {}".format(len(threads)))

        # Start the new thread. Note that index -1 in python yields the last element of
        # the indexed list
        threads[-1].start()

# Launch main() if we are running the script directly, i.e, if we executed python3 udp_server.py 1234 or the like
if __name__ == "__main__":
    main()