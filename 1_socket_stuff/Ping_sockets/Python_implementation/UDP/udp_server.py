# These imports have been already explained before!
import socket, sys, signal

def main():
    # Check we were passed just 1 argument, the port number to bind to!
    if len(sys.argv) != 2:
        print("Use: {} port".format(sys.argv[0]))
        exit(-1)

    # Instantiate a socket with the following characteristics:
        # socket.AF_INET -> IPv4
        # socket.SOCK_DGRAM -> UDP @ the transport layer
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Handler for exiting the program and cleaning up
    # We have defined it here so as to have access to server_socket
    # so that we can close it appropriately. These handlers are passed
    # 2 parameters which we won't use but we need to include them
    # as python won't know how to handle the situation otherwise...
    def k_int_handler(foo, fuu):
        print("Shutting down!")
        server_socket.close()
        exit(0)

    # Bind the above handler to the SIGINT (CTRL + C) signal
    signal.signal(signal.SIGINT, k_int_handler)

    # Bind the socket to the localhost ('127.0.0.1') interface on the provided port
    # We don't have to deal with endiannes conversion like before!
    server_socket.bind(('127.0.0.1', int(sys.argv[1])))

    print("Server ready!")
    # Define the dictionary that'll let us map an incoming message's IP to a given sequence number
    # The index will be a messages source IP and the value will be the corresponding sequence number
    # Hence, a dictionary with only one entry would look like:
        # {'1192.168.1.35': 0}
    proc_2_seq_num = {}
    while True:
        # The socket is blocking by default so we will stay here until we receive a message
        # recvfrom() returns the read message and a tuple containing the messages source address
        # as well as the source port number: (source_ip, source_port)
        # 2048 specifies the maximum data to receive at once, i.e, the buffer size
        message, source_addr = server_socket.recvfrom(2048)

        # Messages returned by recvfrom() and friends are Python bytes objects that need to be
        # decoded to be handled like strings!
        if message.decode() == "Echo request":
            # Check wheteher the source IP is new!
            if not source_addr in proc_2_seq_num:
                # If it us, add a new entry to proc_2_se_num
                proc_2_seq_num[source_addr] = 0

            # Otherwise just increment it
            proc_2_seq_num[source_addr] += 1

            # Send back the reply. Note that just like we decoded the incoming message we need to encode the
            # string we are sending back, converting it into a bytes object in the process which is what
            # socket objects know how to deal with
            server_socket.sendto("Echo reply # {}".format(proc_2_seq_num[source_addr]).encode(), source_addr)

# Launch main() if we are running the script directly, i.e, if we executed python3 udp_server.py 1234 or the like
if __name__ == "__main__":
    main()