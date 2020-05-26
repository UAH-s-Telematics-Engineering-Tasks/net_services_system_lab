#########################################################################################################################
#                                           CERTIFICATE GENERATION                                                      #
#                                                                                                                       #
# Command: openssl req -x509 -nodes -addext "subjectAltName = IP:127.0.0.1" -newkey rsa:4096 \                          #
#                        -keyout key.pem -out cert.pem -days 365                                                        #
#                                                                                                                       #
#     req -> Generate a certificate                                                                                     #
#     -x509 -> Generate a self signed x509 certificate                                                                  #
#     -nodes -> Don't use DES encryption, i.e, don't ask for a password                                                 #
#     -addext "subjectAltName = IP:127.0.0.1" -> Add subject alternative names so tha Chrome accepts the certificate... #
#     -newkey rsa:4096 -> Generate a new RSA 4096 bit key                                                               #
#     -keyout key.pem -> Write the resulting key to key.pem                                                             #
#     -out cert.pem -> Write the certificate to cert.pem                                                                #
#     -days 365 -> Certificate validity                                                                                 #
#                                                                                                                       #
# Taken from: https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl         #
# Note: You need to add the certificate to your browser!                                                                #
#########################################################################################################################

###################################
# Info for finding SSL requests   #
#     RFC 2246 -> Pages 18 and 32 #
###################################

#############################
# Info for Language Headers #
#     RFC 2616 -> Page 104  #
#############################

#########################################################################################################################
#                                                   NOTES                                                               #
#                                                                                                                       #
# Clean the browser's cache regularly as it tends to find out where HTTPS is and that breaks HTTP connectivity...       #
# It may be due to HSTS...                                                                                              #
#########################################################################################################################

########################################################
#                      IMPORTS                         #
#                                                      #
# socket -> Let's us instantiate and work with sockets #
# sys -> Let's us have access to program parameters    #
# select -> Let's us concurrently manage sockets       #
# datetime -> Get the current date to populate headers #
# ssl -> Wrap insecure sockets in a secure context     #
########################################################

import socket, sys, select, datetime, ssl

#########################################################################################################################################
#                                                   RESPONSE TEMPLATES                                                                  #
# These templates are populated when sending responses so that we don't have to write the entire string again and again                 #
# RESPONSE_TEMPLATE -> A typical HTTP response waiting to be filled out with data. It can be used by 200 OK and 404 Not Found responses #
# SECURE REDIRECT -> A 301 Moved Permanently response intended to redirect requests to the insecure HTTP socket to the HTTPS one        #
#########################################################################################################################################

RESPONSE_TEMPLATE = "HTTP/1.1 {}\r\nDate: {}\r\nServer: Dagobah\r\nContent-type: {}\r\nContent-length: {}\r\nConnection: {}\r\n\r\n{}"
SECURE_REDIRECT = 'HTTP/1.1 301 Moved Permanently\r\nLocation: https://127.0.0.1:{}\r\n\r\n<a href="https://127.0.0.1:{}">Moved permanently!</a>'

#######################################################################################################################
#                                                       OPERATION SWITCHES                                            #
#                                                                                                                     #
# These options let the user control how the server behaves                                                           #
# HTTP_ENABLE -> If True we'll accept HTTP connections, these will otherwise be redirected to the HTTPS port          #
# BRWSER_COMPLIANT -> If True we will keep connections alive or terminate them depending on what the browser tells us #
#                     through its headers. If False we will operate in a non-persistent way and close the connection  #
#                     whenever we are done sending and object                                                         #
#######################################################################################################################

HTTP_ENABLE = True
BRWSER_COMPLIANT = False

############################################################################################################################
#                                                   LANGUAGE SUPPORT                                                       #
# This dictionary will let us choose the website to serve depending on the Accept-Language header in the browser's request #
############################################################################################################################

LANGS = {
        'en': 'foo_en.html',
        'es-ES': 'foo_es.html',
        'es': 'foo_es.html',
        'default': 'foo_en.html'
}

def main():
    # Timeout for cleaning inactive sockets. This must be done if operating persistently so that we don't become bloated with
    # sockets... It's given in seconds
    pers_cleanup_timeout = 5

    # Timeout till we print a message notfiying of server inactivity. It's given in seconds
    msg_timeout = 5 * 60

    # This accumulator will let us track the inactivity timeout taking the cleanup one as a reference
    time_acc = 0

    if len(sys.argv) != 2:
        print("Use: {} <binding_port>".format(sys.argv[0]))
        exit(-1)

    ##########################################################################################
    #                                    LIST GLOSSARY                                       #
    #                                                                                        #
    # serv_socks -> Serving sockets, i.e, the HTTP and HTTPS listening sockets               #
    # header_incoming -> Sockets whose header we are still waiting to get                    #
    # incomplete_headers -> A list containing the headers we have not fully received yet     #
    # cnx_socks -> List of connected sockets. This is the one we'll regularly clean up       #
    # sock_stats -> Information regarding sockets contained in cnx_socks. Any given index    #
    #               identifies a socket in cnx_socks and its corresponding information in    #
    #               sock_stats so we must be careful when hadling both lists so that they    #
    #               always stay synched... Each entry is itself a list of two booleans       #
    #               where the first indicates whether the socket has been active recently    #
    #               and the second indicates if we should upgrade this socket from HTTP      #
    #               to HTTPS. We use a boolean to denote inactivity so that recently active  #
    #               sockets are "saved" when cleaning up the incative sockets. An entry like #
    #               [False, False] would indicate the associated socket will be remoeved     #
    #               the next time we run the upkeep functiona and that it should be upgraded #
    #               to a secure connection for example.                                      #
    ##########################################################################################

    serv_socks, header_incoming, incomplete_headers, cnx_socks, sock_stats = [], [], [], [], []

    # Instantiate the appropriate sockets, bind them and listen
    server_setup(serv_socks, int(sys.argv[1]), int(sys.argv[1]) + 1)

    try:
        while True:
            ready_socks = select.select(serv_socks + header_incoming + cnx_socks, [], [], pers_cleanup_timeout)[0]
            # If the timeout is reached an empty list will be returned
            if ready_socks == []:
                # Print an incativity message if we have been inactive for msg_tiemout seconds
                # and reset the clock. Increment the clock otherwise
                if time_acc == msg_timeout:
                    print("We have been inactive for {} seconds".format(msg_timeout))
                    time_acc = 0
                else:
                    time_acc += pers_cleanup_timeout

                # If we have been inactive for pers_cleanup_timeout seconds clean up the connected sockets
                sck_upkeep(cnx_socks, sock_stats)

            else:
                for src in ready_socks:
                    # Reset the inactivity clock
                    time_acc = 0

                    # Handle requests to the HTTP port
                    if src == serv_socks[0]:
                        print("Got an HTTP request!")
                        cnx_socks.append(src.accept()[0])
                        sock_stats.append([True, not HTTP_ENABLE])

                    # Handle requests to the HTTPS port
                    elif src == serv_socks[1]:
                        print("Got an HTTPS request!")
                        try:
                            browser = src.accept()[0]
                        except ssl.SSLError:
                            # We may have been issued an HTTP request or whatever. Just quit to the beginning
                            continue
                        cnx_socks.append(browser)
                        sock_stats.append([True, False])

                    # Handle client requests
                    elif src in cnx_socks:
                        # If we need to upgrade the socket
                        if sock_stats[cnx_socks.index(src)][1]:
                            print("Redirecting HTTP --> HTTPS")

                            # Just empty the socket to be nice to the other party
                            raw_msg = src.recv(8148).decode()

                            # Send the recirect message
                            src.sendall(SECURE_REDIRECT.format(int(sys.argv[1]) + 1, int(sys.argv[1]) + 1).encode())

                            # Remove the socket from the lists, the browser will be given a secure one
                            clean_sck(src, cnx_socks, sock_stats)
                        else:
                            print("Answering a secure request!")

                            # Mark the socket as active!
                            sock_stats[cnx_socks.index(src)][0] = True
                            msg = src.recv(8148).decode()

                            # If the socket hastn't been closed handle the request and produce an approprite response
                            if msg != '':
                                answer_request(src, msg.split('\r\n'), cnx_socks, sock_stats, header_incoming, incomplete_headers)

                            # Remove the socket from our lists otherwise
                            else:
                                clean_sck(src, cnx_socks, sock_stats)

                    # If the request/header hasn't been entirely received (could maybe happen in POST requests...)
                    elif src in header_incoming:
                        print("Building an incomplete header...")

                        # Get the rest of the request
                        msg = browser.recv(8148).decode()
                        if msg != '':
                            # Try to rebuild the request
                            incomplete_headers[header_incoming.index(src)] += msg.split('\r\n')

                            # If the request is now complete we can remove the socket and the
                            # associated info from incomplete headers and header_incoming
                            if answer_request(src, incomplete_headers[header_incoming.index(src)], cnx_socks, sock_stats, header_incoming, incomplete_headers):
                                incomplete_headers.pop(header_incoming.index(src))
                                header_incoming.remove(src)

                        # If for some reason the socket was closed just remove it from our lists
                        else:
                            clean_sck(sck, header_incoming, incomplete_headers)

    # If we get a CTRL + C signal (SIGINT)
    except KeyboardInterrupt:
        print("Quitting...")

        # Clean all the lists and quit
        for sock in serv_socks + header_incoming + cnx_socks:
            sock.close()
        exit(0)

def server_setup(srv_scks, http_port, https_port):
    # Generate a secure context by employing the 'cert.pem' and 'key.pem'
    # we generated earlier (see the top of the document)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile = "cert.pem", keyfile = "key.pem")

    srv_scks.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    # Wrap this socket in a SSL context so that it returs secure sockets on accept()!
    srv_scks.append(context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_side = True))

    # Bind the sockets!
    srv_scks[0].bind(('localhost', http_port))
    srv_scks[1].bind(('localhost', https_port))

    print("Began to listen!")

    # Listen for incoming connections
    srv_scks[0].listen(1)
    srv_scks[1].listen(1)

def sck_upkeep(cnx_scks, sck_stats):
    print("Socket upkeep!\tNumber of connected sockets: {}".format(len(cnx_scks)))

    aux = []

    # Note we SHOULDN'T modify the list we are iterating on... This could have
    # negative implications and yield an unexpected loop
    for info in sck_stats:
        if not info[0]:
            aux.append(sck_stats.index(info))
        else:
            info[0] = False

    # Adjust the list according to the info we gatheres above.
    # aux[-1::-1] reverses the list because if we delete say
    # element i and we then attempt to delete element i + i
    # the index may be out of range... Remember pop() modifies
    # the list in place... The reverse method() wasn't being
    # nice to us...
    for x in aux[-1::-1]:
        sck_stats.pop(x)
        cnx_scks[x].close()
        cnx_scks.pop(x)

def clean_sck(sck, sck_list, sck_data):
    # Send a shutdown signal indicating there will be no more reads or
    # writes to that socket (SHUT_RDWR) so as to be nice to the browser
    # This formality is not imposed on us. Then close the socket and
    # tidy up our lists
    sck.shutdown(socket.SHUT_RDWR)
    sck.close()
    sck_data.pop(sck_list.index(sck))
    sck_list.remove(sck)


def parse_headers(hdrs):
    # This dictionary will hold the headers as the keys and the associated
    # values as the values :). The only exception is the HTTP method which
    # will be identified by the 'request' key. An example entry could be:
    # 'Accept-Language': 'es-ES,en;q=0.5'
    p_hdr = {}

    # Make sure we've got the entire request. As the headers end with '\r\n\r\n'
    # this will translate into 2 empty strings in the last 2 elements of the
    # splitted request!
    if ('GET' in hdrs[0] or 'HEAD' in hdrs[0]) and hdrs[-1] == hdrs[-2] == '':
        p_hdr['request'] = hdrs[0]

        # Ignore the HTTP method and the last 2 empty strings!
        for hdr in hdrs[1:-2]:
            p_hdr[hdr.split(' ', 1)[0][:-1]] = hdr.split(' ', 1)[1]
    return p_hdr

def answer_request(sck, raw_hdrs, cnx_scks, sck_stats, hdr_inc, inc_hdr):
    # Get a dictionary containing the parsed headers
    p_hdrs = parse_headers(raw_hdrs)

    # Remember parse_headers() will return an empty dictionary upon incomplete requests
    if p_hdrs != {}:

        # Check if the browser uses a certain connection scheme and tell serve_content()
        if 'Connection' in p_hdrs:
            if p_hdrs['Connection'] == 'keep-alive' and BRWSER_COMPLIANT:
                serve_content(sck, p_hdrs, 'keep-alive')
            else:
                serve_content(sck, p_hdrs)
                clean_sck(sck, cnx_scks, sck_stats)
        # If we had a 'Connection: close' header or none at all
        else:
            serve_content(sck, p_hdrs)
            clean_sck(sck, cnx_scks, sck_stats)

        # Signal the caller the headers were complete
        return True

    # If they weren't just add the pertaining data to the lists and tell the caller
    else:
        if sck not in hdr_inc:
            hdr_inc.append(sck)
            inc_hdr.append(raw_hdrs)
        return False

def serve_content(sock, p_hdrs, sck_strategy = 'close'):
    # Find out what object was requestested and act accordingly

    # If we were asked for the root weboage
    if p_hdrs['request'].split(' ')[1] == '/':

        # Select the language used for displaying it and open the file
        html_file = open(select_lang(p_hdrs), 'r')
        resp_data = html_file.read()

        # Fill in the template we declared at the beginning but don't send the data yet
        sock.sendall(RESPONSE_TEMPLATE.format('200 OK',
                                              str(datetime.date.today()),
                                              "text/html", len(resp_data),
                                              sck_strategy,
                                              '').encode())

        # If the request used the GET method send the file
        if 'GET' in p_hdrs['request']:
            print("Answered a GET request for the root webpage")
            sock.sendall(resp_data.encode())

        # Otherwise don't do anything else. We must've been issued a HEAD request. Note
        # we still need to open the file as RFC 2616 says the response header MUST be
        # exactly the same as the one we would get with a GET request so we need to know
        # the file's size...
        else:
            print("Answered a HEAD request for the root webpage!")

        # As we always need to open it close the HTML file
        html_file.close()

    # If we are asked for an image serve it in the same fashion as above. Just note the image is
    # opened as a binary file instead of a text based one so ther is no need to encode() when
    # sending it. We should check whether the filename exists or not as this could take our server
    # down but we didn't want to bloat everything with error-checking code... Just assume people
    # are nice.
    elif '.jpg' in p_hdrs['request']:

        # Strip the leading '/' in the filename!
        img = open(p_hdrs['request'].split(' ')[1][1:], 'rb')
        resp_data = img.read()
        sock.sendall(RESPONSE_TEMPLATE.format('200 OK',
                                              str(datetime.date.today()),
                                              "image/jpg", len(resp_data),
                                              sck_strategy,
                                              '').encode())
        if 'GET' in p_hdrs['request']:
            print("Answered a GET request for an image!")
            sock.sendall(resp_data)
        else:
            print("Answered a HEAD request for an image!")
        img.close()

    # If the request is asking for another object just say it's not there and go on.
    # Browsers kept asking for 'favicon.ico' even though it wasn't contained in the
    # HTML file...
    else:
        sock.sendall(RESPONSE_TEMPLATE.format('404 Not Found',
                                              str(datetime.date.today()),
                                              "text/plain", len("Not found!"),
                                              sck_strategy, 
                                              'Not found!').encode())

def select_lang(hdrs):
    # If the browser has some configured preference try to serve the approrpiate page
    if 'Accept-Language' in hdrs:
        aux = {}
        langs = hdrs['Accept-Language'].split(',')
        for lang in langs:

            # If an optin has NO q factor then return it if we have it in LANGS
            if len(lang.split(';')) == 1:
                if lang.strip() in LANGS:
                    return LANGS[lang.strip()]

            # Otherwise just keep track of the q values to leter select the highest one
            else:
                aux[lang.split(';')[0].strip()] = float(lang.split(';')[1].split('=')[1])

        # Generate a sorted list of the languages in the aux dictionary in descending order of preference.
        # sorted() returns a reversed sorted list (note the reverse argument) and it will use the function
        # defined with the lambda keyword to extract a key for comparing. That is, each item will be passed
        # to lambda item: to get the value and then sort it. Remember the items() method returns a 'list' of
        # tuples of the form (key, value). This idea has been taken and then adapted from:
        # https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
        srtd_langs = [lang for lang, vl in sorted(aux.items(), key = lambda item: item[1], reverse = True)]

        # Go through the list to try and serve the most appropriate languges
        for pref_lang in srtd_langs:
            if pref_lang in LANGS:
                return LANGS[pref_lang]

    # Otherwise just return the default webpage
    return LANGS['default']

if __name__ == '__main__':

    # Start the engines!
    main()
