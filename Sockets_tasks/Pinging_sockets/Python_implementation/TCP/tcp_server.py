from socket import *
from threading import *

#Globals!
simul_users = 0
OFF = False

def client_connection (c_socket, addr):
    global simul_users
    global OFF
    disconnect = False
    simul_users += 1
    print("Yay! Got a connection from: ", end="")
    print(addr)
    while True:
        message = c_socket.recv(2048).decode()
        cap_message = message.upper()
        c_socket.send((cap_message).encode())
        if c_socket.recv(2048).decode() == "DISC!":
            print("Disconnect client!")
            if c_socket.recv(2048).decode() == "#0FF!":
                print("Received OFF signal!")
                OFF = True
            simul_users -= 1
            c_socket.close()
            return

def main():
    global simul_users
    global OFF
    server_port = 12000
    threads = []
    #Socket configuration
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1) #Allow 1 user in the queue, reject others!

    print("Ready for connections!")

    while not OFF:
        print("Number of active connections: %d" % (simul_users))
        connection_socket, client_addr = server_socket.accept() #Wait here until you get a new connection!
        threads.append(Thread(target = client_connection, args = (connection_socket, client_addr)))
        print("# of threads: %d" % (len(threads)))
        if not OFF:
            threads[len(threads) - 1].start()
        else:
            connection_socket.close() #Close the last dummy socket!
    print("Closing...")
    for i in range(len(threads) - 1): #Don't wait for the last dummy thread!
        threads[i].join()
    print("Goodbye!")
    server_socket.close()
main()
