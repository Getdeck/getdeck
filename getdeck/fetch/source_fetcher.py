from abc import ABC, abstractmethod
import os
from typing import Optional

import logging
import tempfile

import requests
from git import Repo, GitError

from getdeck.fetch.types import SourceAux, TemporaryData


logger = logging.getLogger("deck")


class FetchError(Exception):
    pass


class SourceFetchBehavior(ABC):
    @abstractmethod
    def fetch(self, data: SourceAux) -> SourceAux:
        pass


class Git(SourceFetchBehavior):
    def fetch(self, data: SourceAux, *args, **kwargs) -> SourceAux:
        location = data.location

        if "#" in location:
            ref, rev = location.split("#")
        else:
            ref = location
            rev = "HEAD"

        rev = kwargs.get("targetRevision", rev)
        path = kwargs.get("path", "")

        temporary_folder = tempfile.mkdtemp()
        path = os.path.join(temporary_folder, path)
        data.path = os.path.dirname(path)
        data.name = os.path.basename(path)
        data.temporary_data = TemporaryData(data=temporary_folder, is_folder=True)

        try:
            repo = Repo.clone_from(ref, temporary_folder)
            repo.git.checkout(rev)
        except GitError as e:
            raise FetchError(f"Cannot checkout {rev} from {ref}: {e}")
        except Exception as e:
            raise e

        return data


class Http(SourceFetchBehavior):
    def fetch(self, data: SourceAux, *args, **kwargs) -> SourceAux:
        temporary_file = tempfile.NamedTemporaryFile(delete=False)
        data.path = os.path.dirname(temporary_file.name)
        data.name = os.path.basename(temporary_file.name)
        data.temporary_data = TemporaryData(data=temporary_file.name, is_file=True)

        try:
            logger.debug(f"Requesting {data.location}")
            with requests.get(data.location, stream=True, timeout=10.0) as res:
                res.raise_for_status()
                for chunk in res.iter_content(chunk_size=4096):
                    if chunk:
                        temporary_file.write(chunk)
                temporary_file.flush()
            temporary_file.close()
        except Exception as e:
            temporary_file.close()
            raise FetchError(
                f"Cannot download Source from http(s) location {data.location}: {e}"
            )

        return data


class Local(SourceFetchBehavior):
    def fetch(self, data: SourceAux, *args, **kwargs) -> SourceAux:
        data.path = os.path.dirname(data.location)
        data.name = os.path.basename(data.location)
        return data


class Content(SourceFetchBehavior):
    def fetch(self, data: SourceAux, *args, **kwargs) -> SourceAux:
        return data  # TODO: remove Content class?


class SourceFetcher:
    def __init__(self, fetch_behavior: SourceFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    @property
    def fetch_behavior(self) -> SourceFetchBehavior:
        return self._fetch_behavior

    @fetch_behavior.setter
    def fetch_behavior(self, fetch_behavior: SourceFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    def fetch(self, data: SourceAux, *args, **kwargs) -> SourceAux:
        data = self._fetch_behavior.fetch(data, *args, **kwargs)
        return data


def select_source_fetch_behavior(source) -> Optional[SourceFetchBehavior]:
    try:
        _ = source.content
        has_content = True
    except Exception:
        has_content = False

    ref = getattr(source, "ref", None)
    if not ref:
        if has_content:
            return Content()
        return None

    if "#" in ref:
        ref, _ = ref.split("#")

    ref_lo = ref.lower()

    if ref_lo.startswith("git") or ref_lo.endswith(".git"):
        return Git()

    if ref_lo.startswith("https") or ref_lo.startswith("http"):
        return Http()

    if ref_lo[0] in "./~":
        return Local()

    return None
