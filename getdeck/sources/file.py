import logging
from operator import methodcaller
import os
import tempfile
from typing import List, Union

import requests
import yaml

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import (
    DeckfileFileSource,
    DeckfileKustomizeSource,
    DeckfileHelmSource,
)
from getdeck.sources.types import K8sSourceFile
from getdeck.utils import sniff_protocol
from git import Repo

logger = logging.getLogger("deck")


class Fetcher:
    def __init__(
        self,
        source: Union[DeckfileFileSource, DeckfileKustomizeSource, DeckfileHelmSource],
        config: ClientConfiguration,
        namespace: str,
    ):
        self.source = source
        self.config = config
        self.namespace = namespace

    @property
    def not_supported_message(self):
        return "Could not fetch source"

    def fetch(self, **kwargs) -> List[K8sSourceFile]:
        handler = methodcaller(f"fetch_{self.type}", **kwargs)
        try:
            return handler(self)
        except NotImplementedError:
            logger.warning(self.not_supported_message)
            return []

    @property
    def type(self) -> str:
        if getattr(self.source, "content", None) is not None:
            return "content"
        protocol = sniff_protocol(self.source.ref)
        return protocol

    def fetch_git(self, **kwargs):
        raise NotImplementedError

    def fetch_http(self, **kwargs):
        raise NotImplementedError

    def fetch_https(self, **kwargs):
        raise NotImplementedError

    def fetch_local(self, **kwargs):
        raise NotImplementedError

    def fetch_content(self, **kwargs):
        raise NotImplementedError


class FileFetcher(Fetcher):
    @property
    def not_supported_message(self):
        return f"Protocol {self.type} not supported for {type(self.source).__name__}"

    def fetch_content(self, **kwargs) -> List[K8sSourceFile]:
        return [K8sSourceFile(name="Deckfile", content=self.source.content)]

    def fetch_http(self, **kwargs) -> List[K8sSourceFile]:
        k8s_workload_files = []
        try:
            logger.debug(f"Requesting file {self.source.ref}")
            with requests.get(self.source.ref, timeout=10.0) as res:
                res.raise_for_status()
                docs = yaml.load_all(res.content, Loader=yaml.FullLoader)

            for doc in docs:
                if doc:
                    k8s_workload_files.append(
                        K8sSourceFile(name=self.source.ref, content=doc)
                    )
            return k8s_workload_files
        except Exception as e:
            logger.error(f"Error loading files from http {e}")
            raise e

    def fetch_https(self, **kwargs):
        return self.fetch_http(**kwargs)

    def fetch_local(self, **kwargs):
        k8s_workload_files = []
        try:
            logger.debug(f"Reading file {self.source.ref}")
            with open(self.source.ref, "r") as input_file:
                docs = yaml.load_all(input_file.read(), Loader=yaml.FullLoader)
            for doc in docs:
                if doc:
                    k8s_workload_files.append(
                        K8sSourceFile(name=self.source.ref, content=doc)
                    )
            return k8s_workload_files
        except Exception as e:
            logger.error(f"Error loading files from http {e}")
            raise e

    def fetch_git(self, **kwargs) -> List[K8sSourceFile]:
        k8s_workload_files = []
        try:
            with tempfile.TemporaryDirectory() as tmp_source:
                logger.debug(f"Cloning from {self.source.ref} to {tmp_source}")

                if not self.source.path:
                    raise Exception("Path to file required.")

                repo = Repo.clone_from(self.source.ref, tmp_source)
                if self.source.targetRevision:
                    repo.git.checkout(self.source.targetRevision)

                file_source = os.path.join(tmp_source, self.source.path)
                with open(file_source, "r") as input_file:
                    docs = yaml.load_all(input_file.read(), Loader=yaml.FullLoader)

                for doc in docs:
                    if doc:
                        k8s_workload_files.append(
                            K8sSourceFile(name=self.source.ref, content=doc)
                        )

            return k8s_workload_files
        except Exception as e:
            logger.error(f"Error loading files from git repository {e}")
            raise e
