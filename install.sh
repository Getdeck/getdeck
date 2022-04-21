#!/bin/bash

download_url=$(curl -L -s https://api.github.com/repos/getdeck/getdeck/releases/latest | grep '"browser_download_url": ".*linux.*"' | grep -Eo "(http|https)://[a-zA-Z0-9./?=_%:-]*")
file_name=$(echo $download_url | grep -oE '[^/]+$')
curl -L $download_url -o /tmp/$file_name
unzip -o /tmp/$file_name -d /tmp/deck
sudo install -o root -g root -m 0755 /tmp/deck/deck /usr/local/bin/deck

# cleanup 
rm -rf /tmp/$file_name
rm -rf /tmp/deck
