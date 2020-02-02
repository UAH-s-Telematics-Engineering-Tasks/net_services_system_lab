import socket, threading, sys, signal

simul_users = 0
thread_kill = False

def client_connection (c_socket, addr):
    global simul_users
    simul_users += 1
    seq_number = 0
    print("Thread started for: {}:{}".format(addr[0], addr[1]))
    while not thread_kill:
        message = c_socket.recv(2048).decode()
        if message == '':
            simul_users -= 1
            c_socket.close()
            return
        elif message == "Echo request":
            seq_number += 1
            try:
                c_socket.send("Echo reply # {}".format(seq_number).encode())
            except:
                print("Socker closed!")
                simul_users -= 1
                c_socket.close()
                return

def main():
    if len(sys.argv) != 2:
        print("Use: {} port".format(sys.argv[0]))
        exit(-1)

    threads = []

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # This function is here so that it 'sees' server_socket to be able to close it!
    def k_int_handler(foo, fuu):
        global thread_kill
        thread_kill = True
        print("Shutting down!")
        for thread in threads: # Don't wait for the last dummy thread!
            thread.join()
        server_socket.close()
        exit(0)

    signal.signal(signal.SIGINT, k_int_handler)

    # Use server_socket.bind('', int(sys.argv[1])) to allow outside connections!
    # '' == sock.INADDR_ANY -> Bind to every interface!
    server_socket.bind(('127.0.0.1', int(sys.argv[1])))
    server_socket.listen(1)

    print("Ready for connections!")

    while True:
        print("Number of active connections: %d" % (simul_users))
        connection_socket, client_addr = server_socket.accept() # Wait here until you get a new connection!
        threads.append(threading.Thread(target = client_connection, args = (connection_socket, client_addr)))
        print("# of threads: {}".format(len(threads)))
        threads[-1].start()

if __name__ == "__main__":
    main()
