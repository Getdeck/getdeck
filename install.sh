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

# Check for install dependency availability
if ! [ -x "$(command -v curl)" ]; then
       echo "❌ curl is required to execute the installation. Please install it and run the installer again!"
       exit
fi
if ! [ -x "$(command -v unzip)" ]; then
       echo "❌ Unzip is required to execute the installation. Please install it and run the installer again!"
       exit
fi
if ! [ -x "$(command -v sudo)" ]; then
       echo "❌ sudo is required to execute the installation. Please install it and run the installer again!"
       exit
fi
if ! [ -x "$(command -v install)" ]; then
       echo "❌ install is required to execute the installation. Please install it and run the installer again!"
       exit
fi

download_url=$(curl -L -s https://api.github.com/repos/getdeck/getdeck/releases/latest | grep '"browser_download_url": ".*'$OS'.*"' | grep -Eo "(http|https)://[a-zA-Z0-9./?=_%:-]*")
file_name=$(echo $download_url | grep -oE '[^/]+$')
curl -L $download_url -o /tmp/$file_name
unzip -o /tmp/$file_name -d /tmp/deck
sudo install -m 0755 /tmp/deck/deck /usr/local/bin/deck

# cleanup 
rm -rf /tmp/$file_name
rm -rf /tmp/deck

# additional information
echo ""
echo "🎉 Getdeck has been successfully installed"
echo ""
echo "🚀 Getting started guide: https://getdeck.dev/docs/getting-started/"
echo "🔧 Intro for Ops: https://getdeck.dev/docs/overview/introduction-for-devops/"
echo "💻 Intro for Devs: https://getdeck.dev/docs/overview/introduction-for-developers/"
echo ""
echo "❓ Any problems? Feel free to give us feedback: https://github.com/Getdeck/getdeck/issues"
echo "Check out our other Kubernetes development tool: https://gefyra.dev"
