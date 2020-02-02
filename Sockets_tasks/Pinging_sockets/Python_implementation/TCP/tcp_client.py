import socket, sys, time, signal, re

def main():
    if len(sys.argv) != 3:
        print("Use: {} IP port".format(sys.argv[0]))
        exit(-1)

    if not re.match(r'(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)\.(\d{1,2}|1\d\d|2[0-4]\d|255)$', sys.argv[1]):
        print("The provided IP address is NOT valid!")
        exit(-1)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def k_int_handler(foo, fuu):
        print("Quitting!")
        client_socket.close()
        exit(0)

    signal.signal(signal.SIGINT, k_int_handler)

    client_socket.connect((sys.argv[1], int(sys.argv[2])))

    while True:
        try:
            client_socket.send("Echo request".encode())
        except:
            k_int_handler(None, None)

        in_msg = client_socket.recv(2048).decode()
        if in_msg == '':
            k_int_handler(None, None)
        print("Echo reply # {}".format(re.findall(r'\d+', in_msg)[0]))
        time.sleep(1)

if __name__ == "__main__":
    main()
