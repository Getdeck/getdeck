import os
import unittest
from pathlib import Path

from getdeck.telemetry.telemetry import CliTelemetry


class TelemetryTest(unittest.TestCase):
    config_pre = "/.deck/config.ini"
    config_post = "/.deck/config.bak.ini"

    def setUp(self):
        home = str(Path.home())
        os.rename(self.config_path, home + self.config_post)
        return super().setUp()

    def tearDown(self) -> None:
        home = str(Path.home())
        os.rename(home + self.config_post, self.config_path)
        return super().tearDown()

    @property
    def config_path(self):
        return str(Path.home()) + self.config_pre

    def _init_tracker(self):
        self.tracker = CliTelemetry()
        # Make sure events are not sent
        self.tracker.tracker.sentry._client.transport = None

    def test_config_file_created(self):
        self.assertFalse(os.path.isfile(self.config_path))
        self._init_tracker()
        self.assertTrue(os.path.isfile(self.config_path))

    def test_config_file_read(self):
        self._init_tracker()
        config = self.tracker.load_config(self.config_path)
        self.assertTrue(config["telemetry"].getboolean("track"))

    def test_opt_out(self):
        self._init_tracker()
        self.tracker.off()
        config = self.tracker.load_config(self.config_path)
        self.assertFalse(config["telemetry"].getboolean("track"))

    def test_opt_in(self):
        self._init_tracker()
        self.tracker.on(test=True)
        config = self.tracker.load_config(self.config_path)
        self.assertTrue(config["telemetry"].getboolean("track"))
