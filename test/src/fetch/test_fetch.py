from unittest import TestCase
from getdeck.deckfile.file import FileSource, InlineSource

from getdeck.fetch.fetch import fetch_data, fetch_source


class FetchSourceTest(TestCase):
    def test_local_inline(self):
        source = InlineSource(content={})
        source_aux = fetch_source(source=source)
        self.assertIsNotNone(source_aux.source)

    def test_local_file(self):
        source = FileSource(ref="./test/resources/file/hello.yaml")
        source_aux = fetch_source(source=source)
        self.assertIsNotNone(source_aux.source)
        self.assertEqual(source_aux.location, "./test/resources/file/hello.yaml")
        self.assertEqual(source_aux.name, "hello.yaml")
        self.assertEqual(source_aux.path, "./test/resources/file")

    def test_git_file(self):
        source = FileSource(
            ref="git@github.com:Getdeck/getdeck.git",
            path="test/resources/test/hello.yaml",
        )
        source_aux = fetch_source(source=source)
        self.assertIsNotNone(source_aux.source)
        self.assertEqual(source_aux.location, "git@github.com:Getdeck/getdeck.git")
        self.assertEqual(source_aux.name, "hello.yaml")
        self.assertIn("/test/resources/test", source_aux.path)


class FetchDataTest(TestCase):
    def test_local_empty(self):
        location = "./test/deckfile/deck.empty.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 1)

    def test_local_inline(self):
        location = "./test/sources/deck.inline.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 2)

    def test_local_file(self):
        location = "./test/sources/deck.file.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 6)

    def test_local_helm(self):
        location = "./test/sources/deck.helm.yaml"
        data_aux = fetch_data(location)
        self.assertIsNotNone(data_aux.deckfile)
        self.assertIsNotNone(data_aux.deckfile_aux)
        self.assertEqual(len(data_aux.source_auxs), 2)

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
