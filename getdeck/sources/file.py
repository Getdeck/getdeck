import logging
import os
from typing import List

import yaml
from getdeck.fetch.types import DeckfileAux, SourceAux

from getdeck.sources.generator import RenderBehavior, RenderError
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


class File(RenderBehavior):
    def _parse_source_file(
        self, ref: str, namespace: str = None
    ) -> List[K8sSourceFile]:
        with open(ref, "r") as input_file:
            docs = yaml.load_all(input_file.read(), Loader=yaml.FullLoader)

        k8s_workload_files = []
        for doc in docs:
            if doc:
                k8s_workload_files.append(
                    K8sSourceFile(name=ref, content=doc, namespace=namespace)
                )
        return k8s_workload_files

    def _parse_source_directory(
        self, ref: str, namespace: str = None
    ) -> List[K8sSourceFile]:
        refs = []

        if not os.path.isdir(ref):
            raise RenderError(f"The provided path does not point to a directory: {ref}")

        extensions = (".yaml", ".yml")
        for file in os.listdir(ref):
            if file.endswith(extensions):
                refs.append(os.path.join(ref, file))

        # parse workloads
        k8s_workload_files = []
        for ref in refs:
            workloads = self._parse_source_file(ref=ref, namespace=namespace)
            k8s_workload_files += workloads

        return k8s_workload_files

    def _parse_source(self, ref: str, namespace: str = None) -> List[K8sSourceFile]:
        if os.path.isdir(ref):
            k8s_workload_files = self._parse_source_directory(
                ref=ref, namespace=namespace
            )
        else:
            k8s_workload_files = self._parse_source_file(ref=ref, namespace=namespace)
        return k8s_workload_files

    def render(
        self, deckfile_aux: DeckfileAux, source_aux: SourceAux, namespace: str = None
    ):
        try:
            source_file = os.path.join(source_aux.path, source_aux.name or "")
            logger.debug(f"Render file {source_file}")
            if not os.path.isabs(source_file):
                source_file = os.path.join(
                    deckfile_aux.path, source_file.removeprefix("./")
                )

            k8s_workload_files = self._parse_source(
                ref=source_file, namespace=namespace
            )
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise e

        return k8s_workload_files
