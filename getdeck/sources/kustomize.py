import logging
import os

import yaml

from getdeck.sources.tooler import ToolerFetcher
from getdeck.sources.types import K8sSourceFile
from getdeck.utils import sniff_protocol

logger = logging.getLogger("deck")


class KustomizeFetcher(ToolerFetcher):
    FILENAME = "manifest.yaml"

    @property
    def type(self) -> str:
        if self.source.ref is None:
            raise RuntimeError("`source.ref` not specified")
        protocol = sniff_protocol(self.source.ref)
        return protocol

    def build_command(self):
        return [
            "kubectl",
            "kustomize",
            self._target(),
            ">",
            f"{self.OUTPUT}/{self.FILENAME}"
        ]

    def collect_workload_files(self):
        k8s_workload_files = []
        with open(os.path.join(self.tmp_output.name, self.FILENAME)) as manifest:
            docs = yaml.load_all(manifest, Loader=yaml.FullLoader)
            for doc in docs:
                if doc:
                    doc_name = f"{doc['kind']}_{doc['metadata']['name']}.yaml"
                    logger.debug(f"Appending resource {doc_name}")
                    k8s_workload_files.append(K8sSourceFile(name=doc_name, content=doc))
        return k8s_workload_files

    def _target(self):
        if self.type == "git":
            return self.source.path
        else:  # http(s)
            return self.source.ref
