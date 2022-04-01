import json
import logging
import os
import tempfile
from typing import List

import yaml

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import DeckfileHelmSource
from getdeck.sources import tooler
from getdeck.sources.types import K8sSourceFile

from git import Repo

from getdeck.utils import sniff_protocol

logger = logging.getLogger("deck")


def fetch_sources_with_git(
    config: ClientConfiguration, source: DeckfileHelmSource, namespace: str = "default"
) -> List[K8sSourceFile]:
    _k8s_version = get_k8s_api_version(config)
    k8s_workload_files = []
    HELM_CMD = []
    HELM_CMD.extend(["helm", "dep", "up", source.path, "&&"])
    HELM_CMD.extend(["helm", "template", f"{source.releaseName}"])
    HELM_CMD.extend([f"{source.path}/"])
    HELM_CMD.extend(["--namespace", namespace])
    if source.valueFiles:
        for _valuefile in source.valueFiles:
            HELM_CMD.extend(["--values", os.path.join(source.path, _valuefile)])
    if source.parameters:
        for parameter in source.parameters:
            HELM_CMD.extend(["--set", f"{parameter.name}={parameter.value}"])
    HELM_CMD.extend(["--output-dir", "/output"])
    HELM_CMD.extend(["--kube-version", _k8s_version, "--api-versions", _k8s_version])
    tmp_source = tempfile.TemporaryDirectory()
    tmp_output = tempfile.TemporaryDirectory()
    try:
        repo = Repo.clone_from(source.ref, tmp_source.name)
        repo.git.checkout(source.targetRevision)
        # run tooler
        tooler.run(
            config,
            HELM_CMD,
            volume_mounts=[f"{tmp_source.name}:/sources", f"{tmp_output.name}:/output"],
        )
        tmp_source.cleanup()

        for root, _dirs, files in os.walk(tmp_output.name):
            for _file in files:
                if _file.endswith(".yaml"):
                    with open(os.path.join(root, _file)) as manifest:
                        # load even multiple documents per file
                        docs = yaml.load_all(manifest, Loader=yaml.FullLoader)
                        for doc in docs:
                            if doc:
                                k8s_workload_files.append(
                                    K8sSourceFile(
                                        name=os.path.join(root, _file), content=doc
                                    )
                                )
        tmp_output.cleanup()
        return k8s_workload_files
    except Exception as e:
        tmp_source.cleanup()
        tmp_output.cleanup()
        raise e


def fetch_sources_from_helm_repo(
    config: ClientConfiguration, source: DeckfileHelmSource, namespace: str = "default"
) -> List[K8sSourceFile]:
    _k8s_version = get_k8s_api_version(config)
    k8s_workload_files = []
    HELM_CMD = []
    HELM_CMD.extend(["helm", "repo", "add", "this", source.ref, "&&"])
    HELM_CMD.extend(
        [
            "helm",
            "template",
            f"{source.releaseName}",
            f"this/{source.chart}",
            "--namespace",
            namespace,
        ]
    )
    if source.parameters:
        for parameter in source.parameters:
            try:
                HELM_CMD.extend(["--set", f"{parameter['name']}={parameter['value']}"])
            except KeyError:
                logger.error(
                    f"The parameters in Deck with ref {source.ref} are malformed"
                )

    HELM_CMD.extend(["--output-dir", "/output"])
    HELM_CMD.extend(["--kube-version", _k8s_version, "--api-versions", _k8s_version])
    if source.helmArgs:
        HELM_CMD.extend(source.helmArgs)
    tmp_output = tempfile.TemporaryDirectory()
    try:
        tooler.run(config, HELM_CMD, volume_mounts=[f"{tmp_output.name}:/output"])

        for root, _dirs, files in os.walk(tmp_output.name):
            for _file in files:
                if _file.endswith(".yaml"):
                    with open(os.path.join(root, _file)) as manifest:
                        # load even multiple documents per file
                        docs = yaml.load_all(manifest, Loader=yaml.FullLoader)
                        for doc in docs:
                            if doc:
                                k8s_workload_files.append(
                                    K8sSourceFile(
                                        name=os.path.join(root, _file), content=doc
                                    )
                                )

        tmp_output.cleanup()
        return k8s_workload_files
    except Exception as e:
        tmp_output.cleanup()
        raise e


def generate_helm_source(
    config: ClientConfiguration, source: DeckfileHelmSource, namespace: str = "default"
) -> List[K8sSourceFile]:
    protocol = sniff_protocol(source.ref)
    if protocol == "git":
        return fetch_sources_with_git(config, source, namespace)
    if protocol in ["http", "https"]:
        files = fetch_sources_from_helm_repo(config, source, namespace)
        return files
    else:
        logger.error("This helm source is currently not supported")
        return []


def get_k8s_api_version(config: ClientConfiguration) -> str:
    req = config.K8S_CORE_API.api_client.request(
        "GET", f"{config.K8S_CORE_API.api_client.configuration.host}/version"
    )
    data = json.loads(req.data)
    return f"{data['major']}.{data['minor']}"
