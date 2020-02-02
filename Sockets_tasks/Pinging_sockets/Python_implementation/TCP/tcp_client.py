from socket import *

shutdown_message = "#0FF!"
server_ip = "192.168.1.36"
server_port = 12000
turn_off = False

def exit(question):
    option = input(question + "(y/n): ")
    option = option.lower()
    if option == 'y':
        return True
    elif option == 'n':
        return False
    else:
        return exit()

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_ip, server_port))

print("Welcome to the remote capitalizator!")

while not turn_off:
    message = input("String to capitalize: ")
    client_socket.send(message.encode())
    cap_sentence = client_socket.recv(2048).decode()
    print("Received cap_sentence: " + cap_sentence)
    turn_off = exit("Quit? ")
    if not turn_off:
        client_socket.send("CONT".encode())
    else:
        client_socket.send("DISC!".encode())
if exit("Shut server? ") == True:
    print("Sending shutdown...")
    client_socket.send(shutdown_message.encode())
    close_socket = socket(AF_INET, SOCK_STREAM)
    close_socket.connect((server_ip, server_port))
    close_socket.close()
client_socket.close()
