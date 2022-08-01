import json
import logging
import os
from functools import cached_property
from typing import List

import yaml

from getdeck.sources.tooler import ToolerFetcher
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


class HelmFetcher(ToolerFetcher):
    @property
    def not_supported_message(self):
        return "This helm source is currently not supported"

    def build_command(self) -> List[str]:
        helm_cmd = self._helm_prep()
        helm_cmd.append("&&")
        helm_cmd.extend(self._helm_with_plugins())
        helm_cmd.extend(self._helm_template())
        helm_cmd.extend(self._helm_source_params())
        helm_cmd.extend(["--output-dir", self.OUTPUT])
        helm_cmd.extend(self._helm_api_versions())
        helm_cmd.extend(self._helm_extra_args())
        return helm_cmd

    def collect_workload_files(self):
        k8s_workload_files = []
        for root, dirs, files in os.walk(self.tmp_output.name):
            dirs.sort()
            for _file in files:
                if _file.endswith(".yaml"):
                    with open(os.path.join(root, _file)) as manifest:
                        # load even multiple documents per file
                        docs = yaml.load_all(manifest, Loader=yaml.FullLoader)
                        for doc in docs:
                            if doc:
                                k8s_workload_files.append(
                                    K8sSourceFile(
                                        name=os.path.join(root, _file),
                                        content=doc,
                                        namespace=self.namespace,
                                    )
                                )
        self.tmp_output.cleanup()
        return k8s_workload_files

    @cached_property
    def k8s_api_version(self) -> str:
        req = self.config.K8S_CORE_API.api_client.request(
            "GET", f"{self.config.K8S_CORE_API.api_client.configuration.host}/version"
        )
        data = json.loads(req.data)
        return f"{data['major']}.{data['minor']}"

    def _helm_prep(self) -> List[str]:
        if self.type == "git":
            return self._helm_dep_up()
        else:  # http(s)
            return self._helm_repo_add()

    def _helm_repo_add(self) -> List[str]:
        return ["helm", "repo", "add", "this", self.source.ref]

    def _helm_dep_up(self) -> List[str]:
        return ["helm", "dep", "up", self.source.path]

    def _helm_with_plugins(self) -> List[str]:
        return ["helm", *(self.source.helmPlugins or [])]

    def _helm_template(self) -> List[str]:
        if self.type == "git":
            temp = [
                "template",
                f"{self.source.releaseName}",
                "--include-crds",
                f"{self.source.path}/",
                "--namespace",
                self.namespace,
            ]
            if self.source.valueFiles:
                for _valuefile in self.source.valueFiles:
                    temp.extend(
                        ["--values", os.path.join(self.source.path, _valuefile)]
                    )
            return temp
        else:  # http(s)
            return [
                "template",
                f"{self.source.releaseName}",
                f"this/{self.source.chart}",
                "--include-crds",
                "--namespace",
                self.namespace,
            ]

    def _helm_source_params(self) -> List[str]:
        params = []
        if self.source.parameters:
            for parameter in self.source.parameters:
                try:
                    val = parameter["value"]
                    if type(val) == bool:
                        val = str(val).lower()
                    params.extend(["--set", f"{parameter['name']}={val}"])
                except KeyError:
                    logger.error(
                        f"The parameters in Deck with ref {self.source.ref} are malformed"
                    )
        return params

    def _helm_api_versions(self) -> List[str]:
        return [
            "--kube-version",
            self.k8s_api_version,
            "--api-versions",
            self.k8s_api_version,
        ]

    def _helm_extra_args(self) -> List[str]:
        return self.source.helmArgs or []
