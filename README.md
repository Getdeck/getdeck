# deck
A CLI that creates reproducible Kubernetes environments for development and testing

<div align="center">
    <img src="https://github.com/Schille/deck/raw/main/docs/static/img/deck-get-1.gif" alt="deck get terminal"/>
</div>

# Installation

## Linux

```
GETDECK=$(curl -L -s https://api.github.com/repos/Schille/deck/releases/latest | grep '"browser_download_url": ".*linux.*"' | grep -Eo "(http|https)://[a-zA-Z0-9./?=_%:-]*") && curl -LO $GETDECK && unzip -o $(echo $GETDECK | grep -oE '[^/]+$') deck && sudo install -o root -g root -m 0755 deck /usr/local/bin/deck
```