from abc import ABC, abstractmethod
import os
from typing import Optional

import logging
import tempfile

import requests
from git import Repo, GitError

from getdeck.fetch.types import DeckfileAux, TemporaryData

logger = logging.getLogger("deck")


class FetchError(Exception):
    pass


class DeckFetchBehavior(ABC):
    @abstractmethod
    def fetch(self, data: DeckfileAux) -> DeckfileAux:
        pass


class Git(DeckFetchBehavior):
    def fetch(self, data: DeckfileAux) -> DeckfileAux:
        location = data.location

        if "#" in location:
            ref, rev = location.split("#")
        else:
            ref = location
            rev = "HEAD"

        temporary_folder = tempfile.mkdtemp()
        data.path = temporary_folder
        data.temporary_data = TemporaryData(data=temporary_folder, is_folder=True)

        try:
            repo = Repo.clone_from(ref, temporary_folder)
            repo.git.checkout(rev)
        except GitError as e:
            del data
            raise FetchError(f"Cannot checkout {rev} from {ref}: {e}")
        except Exception as e:
            del data  # noqa: F821
            raise e

        return data  # noqa: F821


class Http(DeckFetchBehavior):
    def fetch(self, data: DeckfileAux) -> DeckfileAux:
        location = data.location

        temporary_file = tempfile.NamedTemporaryFile(delete=False)
        data.path = os.path.dirname(temporary_file.name)
        data.name = os.path.basename(temporary_file.name)
        data.temporary_data = TemporaryData(data=temporary_file.name, is_file=True)

        try:
            logger.debug(f"Requesting {location}")
            with requests.get(location, stream=True, timeout=10.0) as res:
                res.raise_for_status()
                for chunk in res.iter_content(chunk_size=4096):
                    if chunk:
                        temporary_file.write(chunk)
                temporary_file.flush()
            temporary_file.close()
        except Exception as e:
            temporary_file.close()
            del data
            raise FetchError(
                f"Cannot download Deckfile from http(s) location {location}: {e}"
            )

        return data  # noqa: F821


class DeckFetcher:
    def __init__(self, fetch_behavior: DeckFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    @property
    def fetch_behavior(self) -> DeckFetchBehavior:
        return self._fetch_behavior

    @fetch_behavior.setter
    def fetch_behavior(self, fetch_behavior: DeckFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    def fetch(self, data: DeckfileAux) -> DeckfileAux:
        data = self._fetch_behavior.fetch(data=data)
        return data


def select_deck_fetch_behavior(location: str) -> Optional[DeckFetchBehavior]:
    if "#" in location:
        location, _ = location.split("#")

    location_lo = location.lower()

    if location_lo.startswith("git") or location_lo.endswith(".git"):
        return Git()

    if location_lo.startswith("https") or location_lo.startswith("http"):
        return Http()

    return None
