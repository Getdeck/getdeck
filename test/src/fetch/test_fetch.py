from unittest import TestCase

from getdeck.fetch.fetch import fetch_data


class FetchDataTest(TestCase):
    def test_local(self):
        location = "./test/deckfile/deck.empty.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 1)

    def test_git_with_no_deckfile(self):
        location = "git@github.com:Getdeck/getdeck.git"
        with self.assertRaises(RuntimeError):
            _ = fetch_data(location)

    def test_https(self):
        location = "https://raw.githubusercontent.com/Getdeck/getdeck/main/test/deckfile/deck.empty.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 1)