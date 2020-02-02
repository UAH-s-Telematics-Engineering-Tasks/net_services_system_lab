import socket, sys, re, time

continue_pinging = True

def k_int_handler(foo, fuu):
    global loop_flag
    continue_pinging = False

if __name__ == "__main__":
    if len(sys.argv != 3):
        print("Use: {} IP port".format{sys.argv[0]})

    if not re.match(r'(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)$', sys.arg[1]):
        print("The provided IP address is NOT valid!")
        exit(-1)

    signal.signal(signal.SIGINT, k_int_handler)

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_port = 12000
server_ip = "192.168.1.36" #AF_INET socket family addresses are a tuple (IP or Hostname, port) == (String, Int)
turn_off = False
shutdown_message = "#0FF!"

print("Welcome to the remote capitalizator!")

    while continue_pinging:
        client_socket.sendto("Echo request".encode(), (argv[1], int(argv[2])))
        in_msg, server_addr = client_socket.recvfrom(2048)
        print("Echo reply # {}".format(re.findall(r'\d+', in_msg)[0]))
        
    print("Quitting!")
    client_socket.close()
    exit(0)
