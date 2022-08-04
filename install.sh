#!/bin/bash

OS="`uname`"
case $OS in
	'Linux')
		OS=linux
		echo "Detected Linux! (Congratulations!)"
		;;
	'Darwin')
		OS=darwin
		echo "Detected MacOS"
		;;
	*)
		echo "No supported platform detected"
		exit 1
		;;
esac

download_url=$(curl -L -s https://api.github.com/repos/getdeck/getdeck/releases/latest | grep '"browser_download_url": ".*'$OS'.*"' | grep -Eo "(http|https)://[a-zA-Z0-9./?=_%:-]*")
file_name=$(echo $download_url | grep -oE '[^/]+$')
curl -L $download_url -o /tmp/$file_name
unzip -o /tmp/$file_name -d /tmp/deck
sudo install -m 0755 /tmp/deck/deck /usr/local/bin/deck

# cleanup 
rm -rf /tmp/$file_name
rm -rf /tmp/deck

# additional information
echo -e '\n---\n'
echo -e '🎉 Getdeck has been successfully installed\n'
echo -e '🚀 Getting started guide: https://getdeck.dev/docs/deck/getting-started'
echo -e '🔧 Intro for Ops: https://getdeck.dev/docs/deck/for-devops/intro'
echo -e '💻 Intro for Devs: https://getdeck.dev/docs/deck/for-devs/intro\n'
echo -e '❓ Any problems? Feel free to give us feedback: https://github.com/Getdeck/getdeck/issues\n'
