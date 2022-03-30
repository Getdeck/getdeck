import logging
import os
import tempfile
import traceback
from typing import List

import yaml

from deck.configuration import ClientConfiguration
from deck.deckfile.file import DeckfileHelmSource
from deck.sources import tooler
from deck.sources.types import K8sSourceFile

from git import Repo

from deck.utils import sniff_protocol

logger = logging.getLogger("deck")


def fetch_sources_with_git(config: ClientConfiguration,
                           source: DeckfileHelmSource,
                           namespace: str = "default") -> List[K8sSourceFile]:
    k8s_workload_files = []
    HELM_CMD = []
    HELM_CMD.extend(["helm", "dep", "up", source.path, "&&"])
    HELM_CMD.extend(["helm", "template", f"{source.releaseName}"])
    HELM_CMD.extend([f"{source.path}/"])
    HELM_CMD.extend(["--namespace", namespace])
    if source.valueFiles:
        for _valuefile in source.valueFiles:
            HELM_CMD.extend(["--values", os.path.join(source.path, _valuefile)])
    HELM_CMD.extend(["--output-dir", "/output"])
    tmp_source = tempfile.TemporaryDirectory()
    tmp_output = tempfile.TemporaryDirectory()
    try:
        repo = Repo.clone_from(source.ref, tmp_source.name)
        repo.git.checkout(source.targetRevision)
        # run tooler
        tooler.run(config, HELM_CMD,
                   volume_mounts=
                   [
                       f"{tmp_source.name}:/sources",
                       f"{tmp_output.name}:/output"
                   ]
                   )
        tmp_source.cleanup()

        for root, dirs, files in os.walk(tmp_output.name):
            for _file in files:
                if _file.endswith(".yaml"):
                    with open(os.path.join(root, _file)) as manifest:
                        # load even multiple documents per file
                        docs = yaml.load_all(manifest, Loader=yaml.FullLoader)
                        for doc in docs:
                            k8s_workload_files.append(K8sSourceFile(name=os.path.join(root, _file), content=doc))
        tmp_output.cleanup()
        return k8s_workload_files
    except Exception as e:
        tmp_source.cleanup()
        tmp_output.cleanup()
        raise e


def generate_helm_source(config: ClientConfiguration,
                         source: DeckfileHelmSource,
                         namespace: str = "default") -> List[K8sSourceFile]:
    protocol = sniff_protocol(source.ref)
    if protocol == "git":
        return fetch_sources_with_git(config, source, namespace)

