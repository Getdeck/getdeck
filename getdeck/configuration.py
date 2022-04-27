import os
import sys
import logging


console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)

logger = logging.getLogger("deck")
logger.addHandler(console)

__VERSION__ = "0.5.0"

DECKFILE_FILE = "deck.yaml"


class ClientConfiguration(object):
    def __init__(
        self,
        docker_client=None,
        cluster_name_prefix: str = "",
    ):
        from getdeck.deckfile.selector import deckfile_selector

        if docker_client:
            self.DOCKER = docker_client
        self.TOOLER_BASE_IMAGE = "quay.io/getdeck/tooler"
        self.TOOLER_USER_IMAGE = "deck-tooler"
        self.deckfile_selector = deckfile_selector
        self.CLI_KUBECONFIG_DIRECTORY = os.path.expanduser("~/.deck/")
        if not os.path.exists(self.CLI_KUBECONFIG_DIRECTORY):
            os.mkdir(self.CLI_KUBECONFIG_DIRECTORY)
        self.K3D_CLUSTER_PREFIX = cluster_name_prefix
        self.kubeconfig = None

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
            NetworkingV1Api,
            ApiextensionsV1Api,
        )
        from kubernetes.config import load_kube_config

        if self.kubeconfig:
            load_kube_config(self.kubeconfig)
        else:
            load_kube_config()
        self.K8S_CORE_API = CoreV1Api()
        self.K8S_RBAC_API = RbacAuthorizationV1Api()
        self.K8S_APP_API = AppsV1Api()
        self.K8S_CUSTOM_OBJECT_API = CustomObjectsApi()
        self.K8S_NETWORKING_API = NetworkingV1Api()
        self.K8S_EXTENSION_API = ApiextensionsV1Api()

    def __getattr__(self, item):
        if item in [
            "K8S_CORE_API",
            "K8S_RBAC_API",
            "K8S_APP_API",
            "K8S_CUSTOM_OBJECT_API",
            "K8S_NETWORKING_API",
            "K8S_EXTENSION_API",
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

    def get_k8s_api(self, api_name: str):
        return {
            "CoreV1Api": self.K8S_CORE_API,
            "RbacAuthorizationV1Api": self.K8S_RBAC_API,
            "AppsV1Api": self.K8S_APP_API,
            "CustomObjectsApi": self.K8S_CUSTOM_OBJECT_API,
            "NetworkingV1Api": self.K8S_NETWORKING_API,
            "ApiextensionsV1Api": self.K8S_EXTENSION_API,
        }.get(api_name)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k.isupper()}

    def __str__(self):
        return str(self.to_dict())


default_configuration = ClientConfiguration()
