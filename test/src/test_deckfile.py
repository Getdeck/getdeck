from unittest import TestCase
from getdeck.utils import read_deckfile_from_location


class DeckFileLocationTest(TestCase):
    def test_local(self):
        location = "./test/deckfile/deck.empty.yaml"
        deckfile, working_dir_path, is_temp_dir = read_deckfile_from_location(location)
        self.assertIsNotNone(deckfile)
        self.assertEqual(working_dir_path, "./test/deckfile")
        self.assertFalse(is_temp_dir)

    def test_git_with_no_deckfile(self):
        location = "git@github.com:Getdeck/getdeck.git"
        with self.assertRaises(RuntimeError):
            _ = read_deckfile_from_location(location)

    def test_https(self):
        location = "https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        deckfile, working_dir_path, is_temp_dir = read_deckfile_from_location(location)
        self.assertIsNotNone(deckfile)
        self.assertIsNone(working_dir_path)
        self.assertFalse(is_temp_dir)
