#!/bin/bash

# Get the files from asterisksounds.org
	# Extra English audio files
	sudo wget -O /var/lib/asterisk/sounds/en/extra-en.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/en/download/asterisk-sounds-extra-en-2.9.15.zip

	# Make the directory for Spanish Audio
	sudo mkdir /var/lib/asterisk/sounds/es

	# Get both file packages
	sudo wget -O /var/lib/asterisk/sounds/es/core-es.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/es-ES/download/asterisk-sounds-core-es-ES-2.9.15.zip
	sudo wget -O /var/lib/asterisk/sounds/es/extra-es.zip https://www.asterisksounds.org/sites/asterisksounds.org/files/sounds/es-ES/download/asterisk-sounds-extra-es-ES-2.9.15.zip

# Uncompress everything and clean up!
sudo unzip /var/lib/asterisk/sounds/*/*.zip
sudo rm /var/lib/asterisk/sounds/*/*.zip

# Fix permissions for both languages
sudo chown -R asterisk:asterisk /var/lib/asterisk/sounds
