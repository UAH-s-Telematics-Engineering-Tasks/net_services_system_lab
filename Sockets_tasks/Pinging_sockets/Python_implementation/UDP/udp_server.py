import socket, sys, signal

loop_flag = True

def k_int_handler(foo, fuu):
    global loop_flag
    loop_flag = False

if __name__ == "__main__":
    if len(sys.argv != 2):
        print("Use: {} port".format(argv[0]))
        exit(-1)

    signal.signal(signal.SIGINT, k_int_handler)

    server_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', int(sys.argv[1])))

    print("Server ready!")
    proc_2_seq_num = {}
    while loop_flag:
        message, source_addr = server_socket.recvfrom(2048) #2048 == Buffer size, as the socket can block we saty idle here!
        if message.decode() == "Echo request":
            if not source_addr in proc_2_seq_num:
                proc_2_seq_num[source_addr] = 0
             proc_2_seq_num[source_addr] += 1
             server_socket.sendto("Echo reply # {}".format(proc_2_seq_num[source_addr]), source_addr)
        elif message.decode() == '':
            print("Closing...")
            server_socket.close()
            loop_flag = False
    print("Shutting down!")
