#!/bin/bash

# Get asterisk's source code
sudo wget -O /usr/share/asterisk-17.2.tar.gz https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-17.2.0.tar.gz

# NOTE: We see how we have the "regular" libraries installed and we are missing the development packages. The two versions are suited
# to different needs. The regular library offers the compiled libraries so other programs using them that have been already compiled
# can make the appropriate calls and work as intended. As we want to include the header files themselves we need to have them on our
# system, that's just what the *-dev packages provide: the *.h and *.c (or the equivalent in other languages) to be able to compile
# source code ourselves. That's also why we don't have them by default, it's kind of weird to need them if we are not going to
# compile anything... 

# NOTE: Library pjproject comes bundled with the source and is installed by default as it's tightly coupled with Asterisk's codebase!
# When running configure the --with-pjproject-bundled option is enbled by default since release 15.0.0! We would need to enable it
# otherwise!

# Get the essential dependencies. Check: https://wiki.asterisk.org/wiki/display/AST/System+Libraries
	# Get libjansson -> C library for manipulating JSON data; libjansson4 should be installed!
	# sudo apt install libjansson4
	sudo apt install -y libjansson-dev

	# Get sqlite3 -> Shared library for SQLitev3. SQLite is a DB Management System written in C!; libsqlite3-0 should be installed
        # sudo apt install libsqlite3-0
	sudo apt install -y libsqlite3-dev	

	# Get libxml2 -> XML handling library for GNOME. libxml2 should be installed
	# sudo apt install libxml2
	sudo apt install -y libxml2-dev

	# Get libxslt -> XSLT processing library. XSLT is a processing language for transforming XML docs into other kind of XML docs
	# like HTML or TXT files. libxslt1.1 should be installed!
	# sudo apt install libxslt1.1
	sudo apt install -y libsxlt1-dev

	# Get libncurses -> Use to write text-based UIs in a terminal independent way. Note that libncursesw-* provides wide character
	# support and is installed by default... We'll then get libncurses5-dev.
	# sudo apt install libncurses5
	# sudo apt install libncursesw5
	sudo apt install -y libncurses5-dev
	# sudo apt install libncurses25-dev

	# Get SSL toolkit -> Used to leverage SSL services. The VM has both v1.0.0 and v1.1 installed... We'll try to only use the
	# latest version. We believe libssl-dev corresponds to libssl1.1's dev headers...
	# sudo apt install libssl1.0.0
	# sudo apt install libssl1.0-dev
	# sudo apt install libssl1.1
	sudo apt install -y libssl-dev

	# Get libuuid1 -> Used to manage Universally Unique IDs. Careful as the dev headers come in a pkg with a different name!
	# sudo apt install libuuid1
	sudo apt install -y uuid-dev

	# Get unixodbc -> It implements Open DataBase Connectivity which will be key for later on!
	# sudo apt install libodbc1
	sudo apt install -y unixodbc-dev
	# sudo apt install unixodbc # It may not be neededd but who knows!

	# Get libspeex -> Codec for audio compression especially geared towards human speech
	# sudo apt install libspeex1
	sudo apt install -y libspeex-dev

	# Get libspeexsp -> The extended library for the above
	# sudo apt install libspeexdsp1
	sudo apt install -y libspeexdsp-dev

	# Get libresample -> Real time audio resampling library
	# sudo apt install libresample1
	sudo apt install -y libresample1-dev

	# Get libcurl3 -> Used for getting info from URLs. Current version is libcurl4 so we'll try to use that!
	# sudo apt install libcurl4
	# sudo apt install libcurl3
	sudo apt install -y libcurl4-openssl-dev

	# Get libvorbis -> Coded for audio compression. We believe we only need the development packages
	sudo apt install -y libvorbis-dev

	# Get libogg -> Efficient audio codec for streaming and HD audio
	# sudo apt install libogg0
	sudo apt install -y libogg-dev

	# Get libsrtp -> Secure Real Time Protocol Implementations. Asterisk should support v2.X but it's guarenteed to work with
	# v1.5.4. We'll try our luck with v2.X though!
	# sudo apt install libsrtp2-1
	sudo apt install -y libsrtp2-dev # v2.1.0-1
	# sudo apt install libsrtp0 # v1.4.5
	# sudo apt install libsrtp0-dev #v1.4.5

	# Get libical -> iCalendar data parser. We have versions 3.X and 2.X. We'll try version 3.X
	# sudo apt install libical3
	sudo apt install -y libical-dev

	# Get libiksemel3 -> Implements XMPP, a comms protocol
	# sudo apt install libiksemel3
	sudo apt install -y libiksemel-dev

	# Get libneon -> HTTP and WebDAV client
	# sudo apt install libneon27
	sudo apt install -y libneon27-dev

	# Get libgmime -> MIME parser
	# sudo apt install libgmime-3.0-0
	sudo apt install -y libgmime-3.0-dev 

	# Get libunbound -> Library implementing DNS resolution and validation
	# sudo apt install libunbound2
	sudo apt install -y libunbound-dev

	# Get libedit -> BSD editline and history libraries
	sudo apt install -y libedit-dev
