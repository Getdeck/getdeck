import logging
from operator import methodcaller
from typing import List, Union

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import (
    DeckfileFileSource,
    DeckfileKustomizeSource,
    DeckfileHelmSource,
)
from getdeck.sources.types import K8sSourceFile
from getdeck.utils import sniff_protocol

logger = logging.getLogger("deck")


class FetcherError(Exception):
    pass


class Fetcher:
    def __init__(
        self,
        path: str,
        source: Union[DeckfileFileSource, DeckfileKustomizeSource, DeckfileHelmSource],
        config: ClientConfiguration,
        namespace: str,
        working_dir: str = None
    ):
        self.path = path
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


class FetcherContext:
    def __init__(self, strategy: Fetcher) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Fetcher:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Fetcher) -> None:
        self._strategy = strategy

    def fetch_source_files(self) -> List[K8sSourceFile]:
        source_files = self._strategy.fetch()
        return source_files
