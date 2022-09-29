from unittest import TestCase
from getdeck.configuration import default_configuration
from getdeck.utils import read_deckfile_from_location


class DeckFileLocationTest(TestCase):
    def test_local(self):
        location = "./test/deckfile/deck.empty.yaml"
        deckfile, working_dir_path, is_temp_dir = read_deckfile_from_location(
            location, default_configuration
        )
        self.assertIsNotNone(deckfile)
        self.assertEqual(working_dir_path, "./test/deckfile")
        self.assertFalse(is_temp_dir)
