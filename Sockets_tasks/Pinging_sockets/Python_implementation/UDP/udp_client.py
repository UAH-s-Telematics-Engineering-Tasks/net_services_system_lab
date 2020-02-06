import socket, sys, re, time, signal

# NOTE: Python "swallows" IPs and hostnames. It'll resolve hostnames automagically just by passign it to the socket!

def main():
    continue_pinging = True

    if len(sys.argv) != 3:
        print("Use: {} IP port".format(sys.argv[0]))
        exit(-1)

    if not re.match(r'(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)$', sys.argv[1]):
        print("The provided IP address is NOT valid!")
        exit(-1)

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def k_int_handler(foo, fuu):
        print("Quitting!")
        client_sock.close()
        exit(0)

    signal.signal(signal.SIGINT, k_int_handler)

    while continue_pinging:
        client_sock.sendto("Echo request".encode(), (sys.argv[1], int(sys.argv[2])))
        in_msg, server_addr = client_sock.recvfrom(2048)
        print("Echo reply # {}".format(re.findall(r'\d+', in_msg.decode())[0]))
        time.sleep(1)

if __name__ == "__main__":
    main()
