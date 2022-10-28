import os
import sys
import logging


console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)

logger = logging.getLogger("deck")
logger.addHandler(console)

__VERSION__ = "0.11.0"

DECKFILE_FILE = "deck.yaml"


def fix_pywin32_in_frozen_build() -> None:
    import os
    import site

    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return

    site.addsitedir(sys.path[0])
    customsite = os.path.join(sys.path[0], "lib")
    site.addsitedir(customsite)

    # sys.path has been extended; use final
    # path to locate dll folder and add it to path
    path = sys.path[-1]
    path = path.replace("Pythonwin", "pywin32_system32")
    os.environ["PATH"] += ";" + path

    # import pythoncom module
    import importlib
    import importlib.machinery

    for name in ["pythoncom", "pywintypes"]:
        filename = os.path.join(path, name + "39.dll")
        loader = importlib.machinery.ExtensionFileLoader(name, filename)
        spec = importlib.machinery.ModuleSpec(name=name, loader=loader, origin=filename)
        importlib._bootstrap._load(spec)  # type: ignore


class ClientConfiguration(object):
    def __init__(
        self,
        docker_client=None,
        cluster_name_prefix: str = "",
    ):
        if sys.platform == "win32":
            fix_pywin32_in_frozen_build()
        from getdeck.deckfile.selector import deckfile_selector

        if docker_client:
            self.DOCKER = docker_client
        self.TOOLER_BASE_IMAGE = f"quay.io/getdeck/tooler:{__VERSION__}"
        self.TOOLER_USER_IMAGE = f"deck-tooler:{__VERSION__}"
        self.deckfile_selector = deckfile_selector
        self.CLI_KUBECONFIG_DIRECTORY = os.path.expanduser("~/.deck/")
        if not os.path.exists(self.CLI_KUBECONFIG_DIRECTORY):
            os.mkdir(self.CLI_KUBECONFIG_DIRECTORY)
        self.CLUSTER_PREFIX = cluster_name_prefix
        self.kubeconfig = None
        self.K8S_OBJECT_RETRY = 30
        self.K8S_OBJECT_RETRY_TIMEOUT = 2  # in s

    def _init_docker(self):
        import docker

        try:
            self.DOCKER = docker.from_env()
        except docker.errors.DockerException as de:
            logger.fatal(f"Docker init error: {de}")
            raise docker.errors.DockerException(
                "Docker init error. Docker host not running?"
            )

    def _init_kubeapi(self, context=None):
        from kubernetes.client import (
            CoreV1Api,
            RbacAuthorizationV1Api,
            AppsV1Api,
            CustomObjectsApi,
            NetworkingV1Api,
            ApiextensionsV1Api,
            AdmissionregistrationV1Api,
        )
        from kubernetes.config import load_kube_config

        if self.kubeconfig:
            load_kube_config(self.kubeconfig, context=context)
        else:
            load_kube_config(context=context)
        self.K8S_CORE_API = CoreV1Api()
        self.K8S_RBAC_API = RbacAuthorizationV1Api()
        self.K8S_APP_API = AppsV1Api()
        self.K8S_CUSTOM_OBJECT_API = CustomObjectsApi()
        self.K8S_NETWORKING_API = NetworkingV1Api()
        self.K8S_EXTENSION_API = ApiextensionsV1Api()
        self.K8S_ADMISSION_API = AdmissionregistrationV1Api()

    def __getattr__(self, item):
        if item in [
            "K8S_CORE_API",
            "K8S_RBAC_API",
            "K8S_APP_API",
            "K8S_CUSTOM_OBJECT_API",
            "K8S_NETWORKING_API",
            "K8S_EXTENSION_API",
            "K8S_ADMISSION_API",
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
            "AdmissionregistrationV1Api": self.K8S_ADMISSION_API,
        }.get(api_name)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k.isupper()}

    def __str__(self):
        return str(self.to_dict())


default_configuration = ClientConfiguration()
