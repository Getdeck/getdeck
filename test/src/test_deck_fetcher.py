from unittest import TestCase
from getdeck.fetch.deck_fetcher import (
    DeckFetcher,
    DeckfileAux,
    Git,
    Http,
    select_deck_fetch_behavior,
)


class SelectFetchBehaviorTest(TestCase):
    def test_git(self):
        fetch_behavior = select_deck_fetch_behavior(
            location="git@github.com:Getdeck/getdeck.git"
        )
        self.assertIsInstance(fetch_behavior, Git)

    def test_git_https(self):
        fetch_behavior = select_deck_fetch_behavior(
            location="https://github.com/Getdeck/getdeck.git"
        )
        self.assertIsInstance(fetch_behavior, Git)

    def test_https(self):
        fetch_behavior = select_deck_fetch_behavior(
            location="https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        )
        self.assertIsInstance(fetch_behavior, Http)

    def test_local_dot(self):
        fetch_behavior = select_deck_fetch_behavior(location=".")
        self.assertIsNone(fetch_behavior)

    def test_local_path(self):
        fetch_behavior = select_deck_fetch_behavior(location="./test/deck.yaml")
        self.assertIsNone(fetch_behavior)


class DeckFetcherTest(TestCase):
    def test_default(self):
        location = "git@github.com:Getdeck/getdeck.git"

        data = DeckfileAux(argument_location=location)
        fetch_behavior = select_deck_fetch_behavior(location=location)
        deck_fetcher = DeckFetcher(fetch_behavior=fetch_behavior)
        data = deck_fetcher.fetch(data=data)
        fetch_behavior.clean_up(data=data)
