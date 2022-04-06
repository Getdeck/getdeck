import logging
import tempfile
from typing import List

import requests
import yaml

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import DeckfileFileSource
from getdeck.sources.types import K8sSourceFile
from getdeck.utils import sniff_protocol

logger = logging.getLogger("deck")


def fetch_file_from_http(source: DeckfileFileSource):
    k8s_workload_files = []
    try:
        logger.debug(f"Requesting file {source.ref}")
        with requests.get(source.ref, timeout=10.0) as res:
            res.raise_for_status()
            docs = yaml.load_all(res.content, Loader=yaml.FullLoader)

        for doc in docs:
            if doc:
                k8s_workload_files.append(
                    K8sSourceFile(
                        name=source.ref, content=doc
                    )
                )
        return k8s_workload_files
    except Exception as e:
        logger.error(f"Error loading files from http {e}")
        raise e


def generate_file_source(
    config: ClientConfiguration, source: DeckfileFileSource, namespace: str = "default"
) -> List[K8sSourceFile]:
    print(source)
    if source.content is not None:
        return [K8sSourceFile(name="Deckfile", content=source.content)]
    if source.ref is not None:
        protocol = sniff_protocol(source.ref)
        if protocol in ["http", "https"]:
            return fetch_file_from_http(source)
        else:
            raise RuntimeError(f"Protocol {protocol} not supported for DeckfileFileSource")




