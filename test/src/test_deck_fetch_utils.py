import os
from unittest import TestCase
from getdeck import configuration
from getdeck.deckfile.fetch.utils import get_path_and_name


class GetPathAndNameTest(TestCase):
    def test_name_default(self):
        location = configuration.DECKFILE_FILE
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, configuration.DECKFILE_FILE)

    def test_name_custom(self):
        location = "deck.empty.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.empty.yaml")

    def test_name_yaml(self):
        location = "deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yaml")

    def test_name_yml(self):
        location = "deck.yml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yml")

    def test_path_relative(self):
        location = "./deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yaml")

    def test_path_relative_subfolder(self):
        location = "./path/deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.path.join(os.getcwd(), "path"))
        self.assertEqual(name, "deck.yaml")

    def test_path_relative_parentfolder(self):
        location = "../deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.path.dirname(os.getcwd()))
        self.assertEqual(name, "deck.yaml")

    def test_path_user(self):
        location = "~/deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.path.expanduser("~"))
        self.assertEqual(name, "deck.yaml")

    def test_path_user_subfolder(self):
        location = "~/path/deck.yaml"
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.path.join(os.path.expanduser("~"), "path"))
        self.assertEqual(name, "deck.yaml")

    def test_dot(self):
        location = "."
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yaml")

    def test_empty(self):
        location = ""
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yaml")

    def test_none(self):
        location = None
        path, name = get_path_and_name(location=location)

        self.assertEqual(path, os.getcwd())
        self.assertEqual(name, "deck.yaml")
