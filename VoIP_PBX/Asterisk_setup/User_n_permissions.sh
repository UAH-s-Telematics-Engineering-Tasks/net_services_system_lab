#!/bin/bash

# Install the service file
sudo cp asterisk.service /etc/systemd/system/

# Reload systemd to get the changes
sudo systemctl daemon-reload

# NOTE: The service file runs asterisk as user asterisk belonging to group astrisk!
# Create the user and asterisk groups. The group should be automagically created upon user creation though...
sudo useradd asterisk
sudo groupadd asterisk

# Fix the permissions for the pertinent folder
# Note /var/run/asterisk is created by the unit file
# These runtime directories are reset on boot...
# sudo chown -R asterisk:asterisk /var/run/asterisk
sudo chown -R asterisk:asterisk /var/lib/asterisk
sudo chown -R asterisk:asterisk /usr/lib/asterisk
sudo chown -R asterisk:asterisk /var/spool/asterisk
sudo chown -R asterisk:asterisk /var/log/asterisk
sudo chown -R asterisk:asterisk /usr/sbin/asterisk

# Connecting to the daemon can be done in one of 2 ways
	# Alter the permissions for /var/run/asterisk/asterisk.ctl
		# Add the user who's going to connect to the asterisk group (you need to log out and back!)
		useradd -a -G asterisk vagrant

		# Change the permissions for /var/run/asterisk/asterisk.ctl
		sudo chmod 0771 /var/run/asterisk/asterisk.ctl

		# Connect with asterisk -rvvvvv

	# Run the connection command as asterisk itself
		# Change asterisk's user password: asterisk-asterisk
		echo -e 'asterisk\nasterisk' | sudo passwd asterisk

		# Run the command and enter said password
		su -c 'asterisk -rvvvvv' -l asterisk
