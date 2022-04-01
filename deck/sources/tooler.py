import io
import logging
import os
from typing import List, Union

from deck.configuration import ClientConfiguration

logger = logging.getLogger("deck")


def run(config: ClientConfiguration, cmd: Union[str, List], volume_mounts=None) -> str:
    import docker

    # check if this image is already present on this machine
    try:
        config.DOCKER.images.get(config.TOOLER_USER_IMAGE)
    except docker.errors.ImageNotFound:
        build_user_container(config)
    if type(cmd) == list:
        cmd = " ".join(cmd)
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


def build_user_container(config: ClientConfiguration):
    uid = os.geteuid()
    gid = os.getgid()

    Dockerfile = io.BytesIO(
        (
            f"FROM {config.TOOLER_BASE_IMAGE} "
            + """
    ARG USER_ID
    ARG GROUP_ID
    RUN addgroup -g ${GROUP_ID} -S tooler && adduser -u ${USER_ID} -S tooler -G tooler
    RUN chown ${USER_ID}:${GROUP_ID} /sources
    RUN chown ${USER_ID}:${GROUP_ID} /output
    WORKDIR /sources
    USER tooler
    """
        ).encode("utf-8")
    )
    build_args = {"USER_ID": str(uid), "GROUP_ID": str(gid)}
    # update tooler base image
    # config.DOCKER.images.pull("tooler")
    image, build_logs = config.DOCKER.images.build(
        fileobj=Dockerfile,
        rm=True,
        forcerm=True,
        buildargs=build_args,
        tag=config.TOOLER_USER_IMAGE,
    )
