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


class FetcherError(Exception):
    pass


class Fetcher:
    def __init__(
        self,
        source: Union[DeckfileFileSource, DeckfileKustomizeSource, DeckfileHelmSource],
        config: ClientConfiguration,
        namespace: str,
        working_dir: str,
    ):
        self.source = source
        self.config = config
        self.namespace = namespace
        self.working_dir = working_dir

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

    @staticmethod
    def _parse_source_file(ref: str) -> List[K8sSourceFile]:
        with open(ref, "r") as input_file:
            docs = yaml.load_all(input_file.read(), Loader=yaml.FullLoader)

        k8s_workload_files = []
        for doc in docs:
            if doc:
                k8s_workload_files.append(K8sSourceFile(name=ref, content=doc))
        return k8s_workload_files

    @staticmethod
    def _parse_source_files(refs: List[str]) -> List[K8sSourceFile]:
        k8s_workload_files = []
        for ref in refs:
            workloads = FileFetcher._parse_source_file(ref=ref)
            k8s_workload_files += workloads
        return k8s_workload_files

    @staticmethod
    def _parse_source_directory(ref: str) -> List[K8sSourceFile]:
        refs = []

        if not os.path.isdir(ref):
            raise FetcherError(
                f"The provided path does not point to a directory: {ref}"
            )

        extensions = (".yaml", ".yml")
        for file in os.listdir(ref):
            if file.endswith(extensions):
                refs.append(os.path.join(ref, file))

        # parse workloads
        k8s_workload_files = FileFetcher._parse_source_files(refs=refs)
        return k8s_workload_files

    @staticmethod
    def _parse_source(ref: str, working_dir: str = None) -> List[K8sSourceFile]:
        if working_dir:
            ref = os.path.join(working_dir, ref.removeprefix("./"))
        if os.path.isdir(ref):
            k8s_workload_files = FileFetcher._parse_source_directory(ref=ref)
        else:
            k8s_workload_files = FileFetcher._parse_source_file(ref=ref)
        return k8s_workload_files

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
            logger.error(f"Error loading file from http {e}")
            raise e

    def fetch_https(self, **kwargs):
        return self.fetch_http(**kwargs)

    def fetch_local(self, **kwargs):
        try:
            logger.debug(f"Reading file {self.source.ref}")
            if not os.path.isabs(self.source.ref):
                fpath = os.path.join(
                    self.working_dir, self.source.ref.removeprefix("./")
                )
                k8s_workload_files = self._parse_source(ref=fpath)
            else:
                k8s_workload_files = self._parse_source(ref=self.source.ref)
            return k8s_workload_files
        except Exception as e:
            logger.error(f"Error loading file from http {e}")
            raise e

    def fetch_git(self, **kwargs) -> List[K8sSourceFile]:
        try:
            with tempfile.TemporaryDirectory() as tmp_source:
                logger.debug(f"Cloning from {self.source.ref} to {tmp_source}")

                source_path = ""
                if self.source.path:
                    source_path = self.source.path

                # clone & checkout repository
                repo = Repo.clone_from(self.source.ref, tmp_source)
                if self.source.targetRevision:
                    repo.git.checkout(self.source.targetRevision)

                # file / directory
                tmp_source_path = os.path.join(tmp_source, source_path)
                k8s_workload_files = self._parse_source(ref=tmp_source_path)

            return k8s_workload_files
        except Exception as e:
            logger.error(f"Error loading file(s) from git repository {e}")
            raise e
