<div id="top"></div>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![Coverage Information][coveralls-shield]][coveralls-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Getdeck/getdeck">
    <img src="https://github.com/Getdeck/getdeck/raw/main/docs/static/img/getdeck-components.png" alt="Getdeck components"/>
  </a>

  <h3 align="center">Getdeck</h3>

  <p align="center">
    A CLI that creates reproducible Kubernetes environments for development and testing!
    <br />
    <a href="https://getdeck.dev/docs/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://getdeck.dev/docs/getting-started/">Getting started</a>
    ·
    <a href="https://github.com/Getdeck/getdeck/issues">Report Bug</a>
    ·
    <a href="https://github.com/Getdeck/getdeck/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#running-getdeck">Running Getdeck</a></li>
        <li><a href="#cleaning-up">Cleaning up</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About the project
Getdeck is like docker-compose for Kubernetes: Find a Deckfile that is describing your setup, 
run `deck get ...` and you are ready to work. No Kubernetes knowledge required.

**Simple to use**  
Just install the binary executable `deck` and you are good to go.

**All dependencies managed**  
Helm, kustomize, k3d, kubectl? Getdeck manages all dependencies for your setup so you don't have to.

<p align="right">(<a href="#top">back to top</a>)</p>

### Built with
Getdeck builds on top of the following popular open-source technologies:

### Docker
[*Docker*](https://docker.io) is currently used to run all the required tooling from the Kubernetes ecosystem, so you
don't have to install _everything_ yourself.

### k3d
[*k3d*](https://k3d.io) is supported to run local Kubernetes cluster. 

### kind
[*kind*](https://kind.sigs.k8s.io/) is supported to run local Kubernetes cluster. 

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started
You can easily try Getdeck yourself following this small example.

### Prerequisites
1) Follow the [installation](https://getdeck.dev/docs/installation/) for your preferred platform.

### Running Getdeck
We provide a sophisticated demo project you can deploy locally using `Getdeck`:

```bash
deck get https://github.com/gefyrahq/gefyra-demos.git
```

This might take a few minutes. When it's done, open your browser at
[http://dashboard.127.0.0.1.nip.io:8080/#/workloads?namespace=oauth2-demo](http://dashboard.127.0.0.1.nip.io:8080/#/workloads?namespace=oauth2-demo).
You should see a kubernetes dashboard with some information about the namespace we just deployed using `deck`!

### Cleaning up
To clean it up (i.e. remove the cluster), just run the following command:

```bash
deck remove --cluster https://github.com/gefyrahq/gefyra-demos.git
```

Now go and write your own [Deckfile](https://getdeck.dev/docs/deckfile-specs/)!  

<p align="right">(<a href="#top">back to top</a>)</p>

## Usage
The following actions are available in Getdeck's CLI:
- `get`: setup local development infrastructure, install a [deck](https://getdeck.dev/docs/overview/what-is-a-deck/)
- `remove`: remove Getdeck's development infrastructure and/or just the deck
- `list`: list the available decks of a [Deckfile](https://getdeck.dev/docs/deckfile-specs/)
- `version`: print the current version and exit

_For more examples, please refer to the [CLI documentation](https://getdeck.dev/docs/cli-reference/)_

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- LICENSE -->
## License
Distributed under the Apache License 2.0. See `LICENSE` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

## Reporting Bugs
If you encounter issues, please create a new issue on GitHub or talk to us on the
[Unikube Slack channel](https://unikubeworkspace.slack.com/). 
When reporting a bug please include the following information:

Getdeck version or Git commit that you're running (`deck version`),
description of the bug and logs from the relevant `deck` command (if applicable),
steps to reproduce the issue, expected behavior.  
If you're reporting a security vulnerability, please follow the process for reporting security issues.

## Acknowledgments
Getdeck is sponsored by the [Blueshoe GmbH](https://blueshoe.io).

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Getdeck/getdeck.svg?style=for-the-badge
[contributors-url]: https://github.com/Getdeck/getdeck/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Getdeck/getdeck.svg?style=for-the-badge
[forks-url]: https://github.com/Getdeck/getdeck/network/members
[stars-shield]: https://img.shields.io/github/stars/Getdeck/getdeck.svg?style=for-the-badge
[stars-url]: https://github.com/Getdeck/getdeck/stargazers
[issues-shield]: https://img.shields.io/github/issues/Getdeck/getdeck.svg?style=for-the-badge
[issues-url]: https://github.com/Getdeck/getdeck/issues
[license-shield]: https://img.shields.io/github/license/Getdeck/getdeck.svg?style=for-the-badge
[license-url]: https://github.com/Getdeck/getdeck/blob/master/LICENSE.txt
[coveralls-shield]: https://img.shields.io/coveralls/github/Getdeck/getdeck/main?style=for-the-badge
[coveralls-url]: https://coveralls.io/github/Getdeck/getdeck


