#!/bin/bash

# Get asterisk's source code
sudo wget -O /usr/share/asterisk-17.2.tar.gz https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-17.2.0-rc1.tar.gz

# Get the essential dependencies. Check: https://wiki.asterisk.org/wiki/display/AST/System+Libraries
	# Get libjansson -> C library for manipulating JSON data; libjansson4 should be installed!
	# sudo apt install libjansson4
	sudo apt install libjansson-dev

	# Get sqlite3 -> Shared library for SQLitev3. SQLite is a DB Management System written in C!; libsqlite3-0 should be installed
        # sudo apt install libsqlite3-0
	sudo apt install libsqlite3-dev	

	# Get libxml2 -> XML handling library for GNOME. libxml2 should be installed
	# sudo apt install libxml2
	sudo apt install libxml2-dev

	# Get libxslt -> XSLT processing library. XSLT is a processing language for transforming XML docs into other kind of XML docs like HTML or TXT files. libxslt1.1 should be installed!
	# sudo apt install libxslt1.1
	sudo apt install libsxlt1-dev
