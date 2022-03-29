import os
import sys
import logging

from deck.deckfile.selector import deckfile_selector

console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)

logger = logging.getLogger("deck")
logger.addHandler(console)

__VERSION__ = "0.1.0"

DECKFILE_FILE = "deck.yaml"


class ClientConfiguration(object):
    def __init__(
        self,
        docker_client=None,
    ):
        if docker_client:
            self.DOCKER = docker_client

        self.deckfile_selector = deckfile_selector
        self.CLI_KUBECONFIG_DIRECTORY = os.path.expanduser("~/.deck/")
        self.K3D_CLUSTER_PREFIX = "deck-"

    def _init_docker(self):
        import docker

        try:
            self.DOCKER = docker.from_env()
        except docker.errors.DockerException as de:
            logger.fatal(f"Docker init error: {de}")
            raise docker.errors.DockerException(
                "Docker init error. Docker host not running?"
            )

    def _init_kubeapi(self):
        from kubernetes.client import (
            CoreV1Api,
            RbacAuthorizationV1Api,
            AppsV1Api,
            CustomObjectsApi,
        )
        from kubernetes.config import load_kube_config

        load_kube_config()
        self.K8S_CORE_API = CoreV1Api()
        self.K8S_RBAC_API = RbacAuthorizationV1Api()
        self.K8S_APP_API = AppsV1Api()
        self.K8S_CUSTOM_OBJECT_API = CustomObjectsApi()

    def __getattr__(self, item):
        if item in [
            "K8S_CORE_API",
            "K8S_RBAC_API",
            "K8S_APP_API",
            "K8S_CUSTOM_OBJECT_API",
        ]:
            try:
                return self.__getattribute__(item)
            except AttributeError:
                self._init_kubeapi()
        if item == "DOCKER":
            try:
                return self.__getattribute__(item)
            except AttributeError:
                self._init_docker()

        return self.__getattribute__(item)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k.isupper()}

    def __str__(self):
        return str(self.to_dict())


default_configuration = ClientConfiguration()
