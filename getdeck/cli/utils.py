import logging
import time
from typing import Optional

from getdeck.provider.types import ProviderType

from semantic_version import Version
from getdeck.provider.errors import NotSupportedError

logger = logging.getLogger(__name__)


def stopwatch(func):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = func(*args, **kwargs)
        toc = time.perf_counter()
        logger.debug(
            f"Operation time for '{func.__name__}(...)' was {(toc - tic)*1000:0.4f}ms"
        )
        return result

    return wrapper


def get_active_kube_config_name() -> Optional[str]:
    from kubernetes.config import kube_config
    from kubernetes.client.rest import ApiException

    try:
        _, active_context = kube_config.list_kube_config_contexts()
        return active_context["name"]
    except ApiException:
        return None


def confirm_kube_config(name: str):
    confirm = input(
        f"You are operating with context '{name}'. Do you want to continue? [y/N] "
    )
    if confirm.lower() != "y":
        logger.info("Operation aborted")
        exit()


def get_cluster_initialize_arguments(
    cluster_config, ignore_cluster: bool, no_input: bool
):
    if ignore_cluster or cluster_config is None:
        name = get_active_kube_config_name()
        if not no_input:
            confirm_kube_config(name=name)

        provider_type = ProviderType("kubectlctx")
        native_config = None
    else:
        name = cluster_config.name
        provider_type = ProviderType(cluster_config.provider.lower())
        native_config = cluster_config.nativeConfig

    return provider_type, name, native_config


def install_provider(k8s_provider, cluster_config, do_install: bool, no_input: bool):
    try:
        version = k8s_provider.version()
    except NotSupportedError:
        version = None

    try:
        try:
            if cluster_config.minVersion and version:
                if Version(cluster_config.minVersion) > version:
                    logger.warning(
                        f"{cluster_config.provider} is installed in version {version}, "
                        f"but minVersion is {cluster_config.minVersion}"
                    )
                    if do_install:
                        if not no_input:
                            confirm = input(
                                f"Do you want to update your local {cluster_config.provider}? [y/N] "
                            )
                            if confirm.lower() != "y":
                                logger.info("Operation aborted")
                                exit()
                        k8s_provider.install()
            else:
                logger.debug(
                    f"{cluster_config.provider} is installed in version {version}"
                )
        except FileNotFoundError:
            #  this K8s provider is not yet installed
            logger.warning(
                f"The required cluster provider {cluster_config.provider} is currently not "
                f"installed on your system"
            )
            if do_install:
                if not no_input:
                    confirm = input(
                        f"Do you want to install {cluster_config.provider} on your local system? [y/N] "
                    )
                    if confirm.lower() != "y":
                        logger.info("Operation aborted")
                        exit()
                k8s_provider.install()
    except KeyboardInterrupt:
        print()  # add a newline
        raise RuntimeError("Operation aborted")
