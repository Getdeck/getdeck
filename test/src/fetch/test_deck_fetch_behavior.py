import os
from unittest import TestCase
from getdeck import configuration
from getdeck.fetch.deck_fetcher import DeckfileAux, FetchError, Git, Http


class GitTest(TestCase):
    def test_git(self):
        deckfile_aux = DeckfileAux(location="git@github.com:Getdeck/getdeck.git")

        fetch_behavior = Git()
        deckfile_aux = fetch_behavior.fetch(data=deckfile_aux)

        self.assertTrue(os.path.isdir(deckfile_aux.path))
        self.assertEqual(deckfile_aux.name, configuration.DECKFILE_FILE)

        path = deckfile_aux.path
        del deckfile_aux
        self.assertFalse(os.path.isdir(path))

    def test_branch(self):
        deckfile_aux = DeckfileAux(location="git@github.com:Getdeck/getdeck.git#main")

        fetch_behavior = Git()
        deckfile_aux = fetch_behavior.fetch(data=deckfile_aux)

        self.assertTrue(os.path.isdir(deckfile_aux.path))
        self.assertEqual(deckfile_aux.name, configuration.DECKFILE_FILE)

        path = deckfile_aux.path
        del deckfile_aux
        self.assertFalse(os.path.isdir(path))

    def test_branch_invalid(self):
        deckfile_aux = DeckfileAux(
            location="git@github.com:Getdeck/getdeck.git#invalid"
        )

        fetch_behavior = Git()
        with self.assertRaises(FetchError):
            _ = fetch_behavior.fetch(data=deckfile_aux)

    def test_https(self):
        deckfile_aux = DeckfileAux(location="https://github.com/Getdeck/getdeck.git")

        fetch_behavior = Git()
        deckfile_aux = fetch_behavior.fetch(data=deckfile_aux)

        self.assertTrue(os.path.isdir(deckfile_aux.path))
        self.assertEqual(deckfile_aux.name, configuration.DECKFILE_FILE)

        path = deckfile_aux.path
        del deckfile_aux
        self.assertFalse(os.path.isdir(path))


class HttpTest(TestCase):
    def test_default(self):
        deckfile_aux = DeckfileAux(
            location="https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        )

        fetch_behavior = Http()
        deckfile_aux = fetch_behavior.fetch(data=deckfile_aux)

        self.assertTrue(os.path.isdir(deckfile_aux.path))
        self.assertIsNotNone(deckfile_aux.name)

        location = os.path.join(deckfile_aux.path, deckfile_aux.name)
        del deckfile_aux
        self.assertFalse(os.path.isfile(location))

    def test_url_invalid(self):
        deckfile_aux = DeckfileAux(
            location="https://raw.githubusercontent.com/Getdeck/getdeck/invalid/deck.yaml"
        )

        fetch_behavior = Http()
        with self.assertRaises(FetchError):
            _ = fetch_behavior.fetch(data=deckfile_aux)
