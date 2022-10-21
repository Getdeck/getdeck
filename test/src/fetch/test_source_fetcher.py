from unittest import TestCase
from getdeck.deckfile.file import (
    DeckfileFileSource,
    DeckfileHelmSource,
    DeckfileInlineSource,
)
from getdeck.fetch.source_fetcher import (
    Git,
    Http,
    Local,
    SourceFetcher,
    select_source_fetch_behavior,
)
from getdeck.fetch.types import SourceAux


class SelectSourceFetchBehaviorTest(TestCase):
    def test_git_file_source(self):
        source = DeckfileFileSource(ref="git@github.com:Getdeck/getdeck.git")
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Git)

    def test_git_file_source_https(self):
        source = DeckfileFileSource(ref="https://github.com/Getdeck/getdeck.git")
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Git)

    def test_git_helm_source(self):
        source = DeckfileHelmSource(
            ref="git@github.com:Getdeck/getdeck.git", releaseName="test"
        )
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Git)

    def test_http_file_source(self):
        source = DeckfileFileSource(
            ref="https://raw.githubusercontent.com/Getdeck/getdeck/main/test/sources/resources/hello.yaml"
        )
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Http)

    def test_local_file_source_dot(self):
        source = DeckfileFileSource(ref=".")
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Local)

    def test_local_file_source_path(self):
        source = DeckfileFileSource(ref="./test/hello.yaml")
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsInstance(fetch_behavior, Local)

    def test_none_inline_source(self):
        source = DeckfileInlineSource(content={})
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsNone(fetch_behavior)

    def test_none_helm_source(self):
        source = DeckfileHelmSource(
            ref="https://kubernetes.github.io/dashboard/",
            chart="kubernetes-dashboard",
            releaseName="dashboard",
        )
        fetch_behavior = select_source_fetch_behavior(source=source)
        self.assertIsNone(fetch_behavior)


class SourceFetcherTest(TestCase):
    def test_inline(self):
        location = "https://raw.githubusercontent.com/Getdeck/getdeck/main/test/sources/resources/hello.yaml"
        source = DeckfileFileSource(ref=location)
        source_aux = SourceAux(location=location)
        source_aux.source = source

        fetch_behavior = select_source_fetch_behavior(source=source)
        deck_fetcher = SourceFetcher(fetch_behavior=fetch_behavior)
        source_aux = deck_fetcher.fetch(data=source_aux)
