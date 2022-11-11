from abc import abstractmethod
import io
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from functools import cached_property
from typing import List, Union

from getdeck.configuration import ClientConfiguration
from getdeck.fetch.types import DeckfileAux, SourceAux
from getdeck.sources import tooler
from getdeck.sources.generator import RenderBehavior
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


def run(
    config: ClientConfiguration, cmd: Union[str, List], volume_mounts: List[str] = None
) -> str:
    import docker

    # check if this image is already present on this machine
    try:
        config.DOCKER.images.get(config.TOOLER_USER_IMAGE)
    except docker.errors.ImageNotFound:
        build_user_container(config)
    if type(cmd) == list:
        cmd = " ".join(cmd)

    if gnupg_socket := gnupg_agent_socket_path():
        volume_mounts.extend(
            [
                f"{gnupg_socket}:{gnupg_socket}",
                f"{gnupg_home_path()}:/home/tooler/.gnupg",
            ]
        )

    exec_cmd = f'bash -c "{cmd}"'
    logger.debug("Tooler running with: " + str(exec_cmd))
    logger.debug("Tooler mounted: " + str(volume_mounts))
    content = config.DOCKER.containers.run(
        config.TOOLER_USER_IMAGE,
        exec_cmd,
        volumes=volume_mounts,
        remove=True,
        oom_kill_disable=True,
    )
    return content


def gnupg_home_path() -> str:
    result = subprocess.run("echo $GNUPGHOME", shell=True, stdout=subprocess.PIPE)
    if result.stdout.decode("utf-8").strip():
        return result.stdout.decode("utf-8").strip()
    else:
        return os.path.expanduser("~/.gnupg")


def gnupg_agent_socket_path() -> str:
    """
    :return: the agent socket to mount
    """
    try:
        result = subprocess.run(
            ["gpgconf", "--list-dir", "agent-extra-socket"], stdout=subprocess.PIPE
        )
        return result.stdout.decode("utf-8").strip()
    except FileNotFoundError:
        # gnupg is not installed
        return ""


def build_user_container(config: ClientConfiguration):
    logger.info("Building a local Tooler image for source generation")
    if sys.platform != "win32":
        uid = os.getuid() or 1000
        gid = os.getgid() or 1000
    else:
        uid = 1000
        gid = 1000

    if sys.platform in ["darwin", "win32"]:
        user_group_add = "RUN addgroup -S tooler && adduser -S tooler -G tooler"
    else:
        user_group_add = (
            "RUN getent group ${GROUP_ID} || addgroup -g ${GROUP_ID} -S tooler && "
            "getent passwd ${USER_ID} || adduser -u ${USER_ID} -S tooler -G $(getent group ${GROUP_ID} | cut -d: -f1)"
        )

    Dockerfile = io.BytesIO(
        (
            f"FROM {config.TOOLER_BASE_IMAGE}\n"
            "ARG USER_ID\n"
            "ARG GROUP_ID\n"
            f"{user_group_add}\n"
            "RUN chown ${USER_ID}:${GROUP_ID} /sources\n"
            "RUN chown ${USER_ID}:${GROUP_ID} /output\n"
            "WORKDIR /sources\n"
            "USER tooler\n"
            "ENV HELM_DATA_HOME=/usr/local/share/helm\n"
        ).encode("utf-8")
    )
    build_args = {"USER_ID": str(uid), "GROUP_ID": str(gid)}
    logger.debug(Dockerfile.read().decode("utf-8"))
    # update tooler base image
    # config.DOCKER.images.pull("tooler")
    image, build_logs = config.DOCKER.images.build(
        fileobj=Dockerfile,
        rm=True,
        forcerm=True,
        buildargs=build_args,
        tag=config.TOOLER_USER_IMAGE,
    )


class Tooler(RenderBehavior):
    SOURCES = "/sources"
    OUTPUT = "/output"

    def __init__(self, config: ClientConfiguration, namespace: str):
        super().__init__(config, namespace)
        self.source = None

    def render(
        self, deckfile_aux: DeckfileAux, source_aux: SourceAux, namespace: str = None
    ):
        self.source = source_aux.source
        self.namespace = namespace

        cmd = self.build_command()
        try:
            if source_aux.temporary_data:
                source_path = source_aux.temporary_data.data
            else:
                source_path = source_aux.path

            if source_path:
                if not os.path.isabs(source_path):
                    source_path = os.path.join(
                        deckfile_aux.path, source_path.removeprefix("./")
                    )

                # copy data
                if os.path.isdir(source_path):
                    shutil.copytree(
                        source_path, self.tmp_source.name, dirs_exist_ok=True
                    )
                else:
                    shutil.copy(source_path, self.tmp_source.name)

            logger.debug(f"Render: {source_aux.location}")
            self.run_tooler(cmd)
            source_files = self.collect_workload_files()
            return source_files
        finally:
            self.cleanup()

    @cached_property
    def tmp_output(self):
        return tempfile.TemporaryDirectory()

    @cached_property
    def tmp_source(self):
        return tempfile.TemporaryDirectory()

    def cleanup(self):
        self.tmp_output.cleanup()
        self.tmp_source.cleanup()

    @abstractmethod
    def build_command(self) -> List[str]:
        raise NotImplementedError

    def run_tooler(self, cmd):
        tooler.run(
            self.config,
            cmd,
            volume_mounts=[
                f"{self.tmp_source.name}:{self.SOURCES}",
                f"{self.tmp_output.name}:{self.OUTPUT}",
            ],
        )

    @abstractmethod
    def collect_workload_files(self) -> List[K8sSourceFile]:
        raise NotImplementedError
