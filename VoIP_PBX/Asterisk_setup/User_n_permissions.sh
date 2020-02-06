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
sudo chown -R asterisk:asterisk /var/run/asterisk
sudo chown -R asterisk:asterisk /var/lib/asterisk
sudo chown -R asterisk:asterisk /usr/lib/asterisk
sudo chown -R asterisk:asterisk /var/spool/asterisk
sudo chown -R asterisk:asterisk /var/log/asterisk
sudo chown -R asterisk:asterisk /usr/sbin/asterisk
