from abc import ABC, abstractmethod
import os
from typing import Optional

from pydantic import BaseModel
import logging
import shutil
import tempfile

import requests
from git import Repo, GitError

from getdeck import configuration

logger = logging.getLogger("deck")


class FetchError(Exception):
    pass


class DeckFileData(BaseModel):
    argument_location: str
    cwd: str = os.getcwd()
    path: str = None
    name: str = configuration.DECKFILE_FILE
    working_dir_path: str = None
    is_temp_dir: bool = False


class DeckFetchBehavior(ABC):
    @abstractmethod
    def fetch(self, data: DeckFileData) -> DeckFileData:
        pass

    @abstractmethod
    def clean_up(self, data: DeckFileData):
        pass


class Git(DeckFetchBehavior):
    def fetch(self, data: DeckFileData) -> DeckFileData:
        location = data.argument_location

        if "#" in location:
            ref, rev = location.split("#")
        else:
            ref = location
            rev = "HEAD"

        tmp_dir = tempfile.mkdtemp()
        data.path = tmp_dir
        data.working_dir_path = tmp_dir
        data.is_temp_dir = True

        try:
            repo = Repo.clone_from(ref, tmp_dir)
            repo.git.checkout(rev)
        except GitError as e:
            self.clean_up(data=data)
            raise FetchError(f"Cannot checkout {rev} from {ref}: {e}")
        except Exception as e:
            self.clean_up(data=data)
            raise e

        return data

    def clean_up(self, data: DeckFileData):
        shutil.rmtree(data.working_dir_path)


class Http(DeckFetchBehavior):
    def fetch(self, data: DeckFileData) -> DeckFileData:
        location = data.argument_location

        download = tempfile.NamedTemporaryFile(delete=False)
        data.path = os.path.dirname(download.name)
        data.name = os.path.basename(download.name)

        try:
            logger.debug(f"Requesting {location}")
            with requests.get(location, stream=True, timeout=10.0) as res:
                res.raise_for_status()
                for chunk in res.iter_content(chunk_size=4096):
                    if chunk:
                        download.write(chunk)
                download.flush()
            download.close()
        except Exception as e:
            download.close()
            self.clean_up(data=data)
            raise FetchError(
                f"Cannot download Deckfile from http(s) location {location}: {e}"
            )

        return data

    def clean_up(self, data: DeckFileData):
        os.remove(os.path.join(data.path, data.name))


class DeckFetcher:
    def __init__(self, fetch_behavior: DeckFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    @property
    def fetch_behavior(self) -> DeckFetchBehavior:
        return self._fetch_behavior

    @fetch_behavior.setter
    def fetch_behavior(self, fetch_behavior: DeckFetchBehavior) -> None:
        self._fetch_behavior = fetch_behavior

    def fetch(self, data: DeckFileData) -> DeckFileData:
        data = self._fetch_behavior.fetch(data=data)
        return data


def select_fetch_behavior(location: str) -> Optional[DeckFetchBehavior]:
    if "#" in location:
        location, _ = location.split("#")

    location_lo = location.lower()

    if location_lo.startswith("git") or location_lo.endswith(".git"):
        return Git()

    if location_lo.startswith("https") or location_lo.startswith("http"):
        return Http()

    return None
