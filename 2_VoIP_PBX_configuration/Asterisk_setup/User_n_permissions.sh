#!/bin/bash

# Install the service file
sudo cp asterisk.service /etc/systemd/system/

# Reload systemd to get the changes
sudo systemctl daemon-reload

# Start the service manually with: sudo systemctl start asterisk
# Uncomment the following line to enable it on boot
# sudo systemctl enable asterisk

# The service file runs asterisk as user asterisk belonging to group astrisk!
# Create the user and asterisk groups. The group should be automagically created upon user creation though...
sudo useradd asterisk
sudo groupadd asterisk

# Fix the permissions for the pertinent folders
# Note /var/run/asterisk is created by the unit file
# as runtime directories are reset on boot...

# We might need to manually adjust the permissions of /var/log/asterisk
# after the first run... File Master.csv was created belonging to root:root
# on our installation...

sudo chown -R asterisk:asterisk /var/lib/asterisk
sudo chown -R asterisk:asterisk /usr/lib/asterisk
sudo chown -R asterisk:asterisk /var/spool/asterisk
sudo chown -R asterisk:asterisk /var/log/asterisk
sudo chown -R asterisk:asterisk /usr/sbin/asterisk


# Connecting to the daemon can be done in one of 2 ways
	# Alter the permissions for /var/run/asterisk/asterisk.ctl
		# Add the user who's going to connect to the asterisk group (you need to log out and back!)
		# useradd -a -G asterisk vagrant

		# Change the permissions for /var/run/asterisk/asterisk.ctl
		# sudo chmod 0771 /var/run/asterisk/asterisk.ctl

		# Connect with asterisk -rvvvvv

	# Run the connection command as asterisk itself
		# Change asterisk's user password: asterisk-asterisk
		# echo -e 'asterisk\nasterisk' | sudo passwd asterisk

		# Run the command and enter said password
		# su -c 'asterisk -rvvvvv' -l asterisk
