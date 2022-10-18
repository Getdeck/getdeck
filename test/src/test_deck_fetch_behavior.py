import os
from unittest import TestCase
from getdeck import configuration
from getdeck.deckfile.fetch.deck_fetcher import DeckfileAux, FetchError, Git, Http


class GitTest(TestCase):
    def test_git(self):
        data = DeckfileAux(argument_location="git@github.com:Getdeck/getdeck.git")

        fetch_behavior = Git()
        data = fetch_behavior.fetch(data=data)

        self.assertTrue(os.path.isdir(data.path))
        self.assertIsNotNone(data.working_dir_path)
        self.assertEqual(data.name, configuration.DECKFILE_FILE)

        fetch_behavior.clean_up(data=data)
        self.assertFalse(os.path.isdir(data.working_dir_path))

    def test_branch(self):
        data = DeckfileAux(argument_location="git@github.com:Getdeck/getdeck.git#main")

        fetch_behavior = Git()
        data = fetch_behavior.fetch(data=data)

        self.assertTrue(os.path.isdir(data.path))
        self.assertIsNotNone(data.working_dir_path)
        self.assertEqual(data.name, configuration.DECKFILE_FILE)

        fetch_behavior.clean_up(data=data)
        self.assertFalse(os.path.isdir(data.working_dir_path))

    def test_branch_invalid(self):
        data = DeckfileAux(
            argument_location="git@github.com:Getdeck/getdeck.git#invalid"
        )

        fetch_behavior = Git()
        with self.assertRaises(FetchError):
            data = fetch_behavior.fetch(data=data)

    def test_https(self):
        data = DeckfileAux(argument_location="https://github.com/Getdeck/getdeck.git")

        fetch_behavior = Git()
        data = fetch_behavior.fetch(data=data)

        self.assertTrue(os.path.isdir(data.path))
        self.assertIsNotNone(data.working_dir_path)
        self.assertEqual(data.name, configuration.DECKFILE_FILE)

        fetch_behavior.clean_up(data=data)
        self.assertFalse(os.path.isdir(data.working_dir_path))


class HttpTest(TestCase):
    def test_default(self):
        data = DeckfileAux(
            argument_location="https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        )

        fetch_behavior = Http()
        data = fetch_behavior.fetch(data=data)

        self.assertTrue(os.path.isdir(data.path))
        self.assertIsNone(data.working_dir_path)
        self.assertIsNotNone(data.name)

        fetch_behavior.clean_up(data=data)
        self.assertFalse(os.path.isfile(os.path.join(data.path, data.name)))

    def test_url_invalid(self):
        data = DeckfileAux(
            argument_location="https://raw.githubusercontent.com/Getdeck/getdeck/invalid/deck.yaml"
        )

        fetch_behavior = Http()
        with self.assertRaises(FetchError):
            _ = fetch_behavior.fetch(data=data)
