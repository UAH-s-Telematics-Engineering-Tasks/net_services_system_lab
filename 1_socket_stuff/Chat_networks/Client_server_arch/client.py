import socket, sys, select, time

#####################################################################
#                           Imports                                 #
# time -> Let's us introduce the needed delays when sending images! #
#####################################################################

# NOTE: The socket module has a sendfile() method but we decided to manually do it ourselves.
# NOTE: At least for the first time...

#############################################################################################
#                              How cool are ANSI Escape Sequences?                          #
# ANSI Escape Sequences are, as their name implies, special sequences that we can print     #
# to a terminal to control its behavior instead of showing characters on screen. You can    #
# find a very comprehensive table over at https://en.wikipedia.org/wiki/ANSI_escape_code.   #
# We have used the following sequences which can be found in the aforementioned site:       #
#           ESC[nF -> Move the cursor to the beginning of the line n lines up               #
#           ESC[nG -> Move the cursor to column n in the current line                       #
#           ESC[2K -> Erase the entire line without changing the cursor¡s position          #
# Note the ESC character is given by 0x1B or 27 as seen in the ASCII table, that's why      #
# you see the leading \x1B in these sequences. Tradition has it that we use the octal       #
# equivalent, \033, but we are more of the "hexy" kind... Combining these escape sequences  #
# with the program flow we have amanged to build a more visually appealing CLI for our chat #
# client but it's still not as robust as we would like it to be...                          #
#############################################################################################

def main():
    if len(sys.argv) != 4:
        print("Use: {} <server_IP> <server_port> <username>".format(sys.argv[0]))
        exit(-1)
    elif sys.argv[3] == 'serving_sock':
        print("This username is restricted... Use another one!")
        exit(-1)

    # CLI Stuff
    prompt = 'Type something --> '
    clear_prompt = "\x1B[1G" + "\x1B[2K"
    clear_input = "\x1B[1F" + "\x1B[2K"

    # We could also use this clear_prompt sequence depending on our taste!
    # clear_prompt = "\x1B[" + str(len(prompt)) + "D" + "\x1B[2K"

    # Set up our connection socket
    info_sources = [socket.socket(socket.AF_INET, socket.SOCK_STREAM), sys.stdin]
    info_sources[0].connect((sys.argv[1], int(sys.argv[2])))

    # Send the username as soon as you connect so that the server can move on!
    info_sources[0].sendall(sys.argv[3].encode())

    print("We're connected to -> {}:{}".format(sys.argv[1], sys.argv[2]))

    # Variables for controlling image sending and reception
    inc_file = None
    reading_file = False
    rcv_bytes = 0

    try:
        while True:

            # If we are receiving an image don't write the prompt. Note we are flushing it because there
            # is no trailing newline ('\n'). Most terminals won't clear the buffers until they see one...
            if not reading_file:
                print(prompt, end = '', flush = True)
            for src in select.select(info_sources, [], [])[0]:

                # If the user has typed a message
                if src == sys.stdin:

                    # Read it
                    inc_msg = sys.stdin.readline().rstrip()

                    # If they want to send an image
                    if "send_img" in inc_msg:

                        # Open it up for reading IN BINARY after getting the filename
                        f_name = inc_msg.split(' ')[1]
                        img = open(f_name, 'rb')
                        img_data = img.read()

                        # Inform the server and clients that you're about to send an image and its lenght
                        info_sources[0].sendall(("IMG_INCOMING!;" + str(len(img_data))).encode())

                        # Wait to make sure TCP buffers are cleared!
                        time.sleep(0.1)

                        # Send all the data
                        info_sources[0].sendall(img_data)

                        # Close the file and move on
                        img.close()

                    # If we are not sending an image
                    else:
                        # Build the output message by appending your username
                        out_msg = sys.argv[3] + " -> " + inc_msg

                        # Print the message to your own screen
                        print(clear_input + out_msg)

                        # Ans send it to the server
                        info_sources[0].sendall(out_msg.encode())

                # If we are receiving a message
                else:
                    # And it's not a file
                    if not reading_file:

                        # We can safely decode it
                        i_msg = info_sources[0].recv(8148).decode()

                        # The server has either kicked us out or gone down, just quit
                        if i_msg == '':
                            raise KeyboardInterrupt

                        # If an image is about to come
                        elif 'IMG_INCOMING!' in i_msg:

                            # Get the total incoming bytes
                            rcv_bytes = int(i_msg.split(';')[1])

                            # Tell the user
                            print(clear_prompt + "Image incoming!\tSize: {}".format(rcv_bytes))

                            # Open a file for storing the incoming data
                            inc_file = open("rcv_img.jpg", 'wb')

                            # And activate the reading mode, again, to prevent decoding illegal bytes
                            reading_file = True

                        # If there is no file coming just print the message
                        else:
                            print(clear_prompt + i_msg)

                    # While we are reading an image
                    else:

                        # Read the data without attempting to decode it
                        i_msg = info_sources[0].recv(8148)

                        # Keep track of the received bytes
                        rcv_bytes -= len(i_msg)

                        # Write the data to the opened file
                        inc_file.write(i_msg)

                        # When finished just close the file and deactivate the "image mode"
                        if rcv_bytes == 0:
                            reading_file = False
                            inc_file.close()

    # If we receive CTRL + C or the server tears down our connection
    except KeyboardInterrupt:
        print("Quitting...")

        # Close our socket and just quit
        info_sources[0].close()
        exit(0)

if __name__ == "__main__":
    main()