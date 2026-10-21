"""Regression tests for the Collab compiler and its PlantUML backend.

Run from the repository root:
    python3 -m unittest discover -s tests -v

No PlantUML executable or third-party Python packages are required.
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "src" / "collabc.py"
FLY = ROOT / "examples" / "flyNshoot.collab"
RAIN = ROOT / "examples" / "rain-gauge.collab"

spec = importlib.util.spec_from_file_location("collabc", COMPILER)
collabc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = collabc
spec.loader.exec_module(collabc)


class CompilerRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fly = collabc.parse_model(FLY)
        cls.puml = collabc.generate_puml(cls.fly, FLY.name)

    def test_flynshoot_semantics(self):
        self.assertEqual(len(self.fly.aos), 8)
        self.assertEqual(len(self.fly.collaborations), 13)
        self.assertEqual(len(list(collabc.unique_signals(self.fly))), 20)
        self.assertEqual(self.fly.roles["Mine"], "HSM")
        self.assertEqual(self.fly.roles["Player"], "EXTERNAL")
        self.assertEqual(self.fly.roles["TickTimer"], "TIMER")

    def test_valid_plantuml_envelope_and_newlines(self):
        lines = self.puml.splitlines()
        self.assertEqual(lines[0], "@startuml")
        self.assertEqual(lines[-1], "@enduml")
        self.assertGreater(len(lines), 50)
        self.assertEqual(self.puml.count("@startuml"), 1)
        self.assertEqual(self.puml.count("@enduml"), 1)
        self.assertNotIn(r"\\n@enduml", self.puml)

    def test_local_timer_occurrences_and_legend(self):
        self.assertEqual(self.puml.count('usecase "<b>T</b>'), 5)
        for receiver in ("Ship", "Missile", "Tunnel"):
            self.assertIn(f"TickTimer__{receiver} -right-> {receiver}", self.puml)
        for timer in ("BlinkTimer", "ScreenTimer"):
            self.assertIn(f"{timer} -right-> Tunnel", self.puml)
        self.assertEqual(self.puml.count("legend bottom"), 1)
        self.assertEqual(self.puml.count("| <b>T</b> TickTimer | repeat; 30ms | TIME_TICK |"), 1)
        self.assertIn("| <b>T</b> BlinkTimer | one-shot; 5s | BLINK_TIMEOUT |", self.puml)
        self.assertIn("| <b>T</b> ScreenTimer | one-shot; 5s | SCREEN_TIMEOUT |", self.puml)

    def test_bidirectional_collaborations_have_receiver_headings(self):
        for a, b in (("Ship", "Missile"), ("Ship", "Tunnel"), ("Tunnel", "Mine")):
            self.assertIn(f"{a} <--> {b}\\nnote on link", self.puml)
            self.assertIn(f"  <b>-> {a}</b>", self.puml)
            self.assertIn(f"  <b>-> {b}</b>", self.puml)
        self.assertNotIn("Ship --> Tunnel\\nnote on link", self.puml)
        self.assertNotIn("Tunnel --> Ship\\nnote on link", self.puml)

    def test_unidirectional_collaborations_use_signal_only_notes(self):
        self.assertIn("Player --> Tunnel\\nnote on link\\n  PLAYER_TRIGGER\\n  PLAYER_QUIT\\nend note", self.puml)
        self.assertIn("Mine --> Ship\\nnote on link\\n  HIT_MINE\\nend note", self.puml)
        self.assertNotIn("  Player -> Tunnel", self.puml)
        self.assertNotIn("  Mine -> Ship", self.puml)

    def test_deterministic_generation(self):
        self.assertEqual(self.puml, collabc.generate_puml(self.fly, FLY.name))
        self.assertEqual(self.puml, collabc.generate_puml(collabc.parse_model(FLY), FLY.name))

    def test_rain_gauge_is_not_special_cased(self):
        rain = collabc.parse_model(RAIN)
        puml = collabc.generate_puml(rain, RAIN.name)
        self.assertIn("BucketSensorAO --> ControlAO", puml)
        self.assertIn("  BUCKET_TIPPED", puml)
        self.assertNotIn("legend bottom", puml)
        self.assertNotIn('usecase "<b>T</b>', puml)

    def test_cli_generates_parseable_multiline_output(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(COMPILER), str(FLY), "--puml-only",
                 "--out-dir", directory],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            path = Path(directory) / "flyNshoot.puml"
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_text(encoding="utf-8"), self.puml)
            self.assertFalse((Path(directory) / "flyNshoot-signals.hpp").exists())


if __name__ == "__main__":
    unittest.main()
