"""Regression tests for logical external participants and legacy ISR support."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collabc import ModelError, generate_puml, generate_signals_hpp, parse_model


class ExternalParticipantsTests(unittest.TestCase):
    def parse(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.collab"
            path.write_text(source, encoding="utf-8")
            return parse_model(path)

    def test_external_is_actor_and_collaboration_remains_directional(self):
        model = self.parse("""collab 1
external User
ao Table
collaboration User Table
  User -> Table
    PAUSE
    SERVE
end
""")
        self.assertEqual(model.roles["User"], "EXTERNAL")
        self.assertEqual(model.roles["Table"], "AO")
        puml = generate_puml(model, "sample.collab")
        self.assertIn('actor "User" as User', puml)
        self.assertIn('component "<size:17><b>Table</b></size>" as Table <<AO>>', puml)
        self.assertIn("User --> Table", puml)
        self.assertIn("    PAUSE", puml)
        header = generate_signals_hpp(model, "sample.collab", "AppSignals", "MAX_APP_SIG")
        self.assertIn("PAUSE_SIG = QP::Q_USER_SIG", header)
        self.assertIn("SERVE_SIG", header)

    def test_isr_remains_supported(self):
        model = self.parse("""collab 1
isr TickISR
ao Controller
collaboration TickISR Controller
  TickISR -> Controller
    TICK
end
""")
        self.assertEqual(model.roles["TickISR"], "ISR")
        self.assertIn('<<ISR>>', generate_puml(model, "sample.collab"))

    def test_external_name_must_be_unique(self):
        with self.assertRaisesRegex(ModelError, "duplicate participant"):
            self.parse("""collab 1
external User
ao User
collaboration User Table
  User -> Table
    PAUSE
end
""")

    def test_external_name_must_be_identifier(self):
        with self.assertRaisesRegex(ModelError, "invalid participant name"):
            self.parse("""collab 1
external Bad-Name
ao Table
collaboration Bad-Name Table
  Bad-Name -> Table
    PAUSE
end
""")


if __name__ == "__main__":
    unittest.main()
