from unittest import TestCase

from getdeck.fetch.fetch import fetch_data


class DeckFileLocationTest(TestCase):
    def test_local(self):
        location = "./test/deckfile/deck.empty.yaml"
        deckfile, working_dir_path, is_temp_dir = fetch_data(location)
        self.assertIsNotNone(deckfile)
        self.assertEqual(working_dir_path, "./test/deckfile")
        self.assertFalse(is_temp_dir)

    def test_git_with_no_deckfile(self):
        location = "git@github.com:Getdeck/getdeck.git"
        with self.assertRaises(RuntimeError):
            _ = fetch_data(location)

    def test_https(self):
        location = "https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        deckfile, working_dir_path, is_temp_dir = fetch_data(location)
        self.assertIsNotNone(deckfile)
        self.assertIsNone(working_dir_path)
        self.assertFalse(is_temp_dir)
