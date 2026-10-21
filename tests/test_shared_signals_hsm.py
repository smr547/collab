"""Regression tests for passive HSM participants and shared signal identities."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collabc import ModelError, generate_puml, generate_signals_hpp, parse_model, unique_signals


class SharedSignalsAndHsmTests(unittest.TestCase):
    def parse(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.collab"
            path.write_text(source, encoding="utf-8")
            return parse_model(path)

    def test_one_signal_multiple_receivers_and_hsm_stereotype(self):
        model = self.parse("""collab 1
timer TickTimer
ao Ship
ao Missile
ao Tunnel
hsm Mine
collaboration TickTimer Ship
  TickTimer -> Ship
    TIME_TICK
end
collaboration TickTimer Missile
  TickTimer -> Missile
    TIME_TICK
end
collaboration TickTimer Tunnel
  TickTimer -> Tunnel
    TIME_TICK
end
collaboration Tunnel Mine
  Tunnel -> Mine
    TIME_TICK
end
""")
        self.assertEqual(model.roles["Mine"], "HSM")
        self.assertEqual(list(unique_signals(model)), [
            ("TIME_TICK", [
                ("TickTimer", "Ship"),
                ("TickTimer", "Missile"),
                ("TickTimer", "Tunnel"),
                ("Tunnel", "Mine"),
            ])
        ])
        puml = generate_puml(model, "sample.collab")
        self.assertIn('component "Mine" as Mine <<HSM>>', puml)
        self.assertIn("Tunnel --> Mine", puml)
        header = generate_signals_hpp(model, "sample.collab", "AppSignals", "MAX_APP_SIG")
        self.assertEqual(header.count("TIME_TICK_SIG"), 1)
        self.assertIn("//   Tunnel -> Mine", header)

    def test_duplicate_signal_within_same_flow_is_rejected(self):
        with self.assertRaisesRegex(ModelError, "duplicate signal 'TIME_TICK'"):
            self.parse("""collab 1
ao Ship
timer TickTimer
collaboration TickTimer Ship
  TickTimer -> Ship
    TIME_TICK
    TIME_TICK
end
""")

    def test_hsm_name_must_be_unique(self):
        with self.assertRaisesRegex(ModelError, "duplicate participant"):
            self.parse("""collab 1
ao Mine
hsm Mine
ao Tunnel
collaboration Tunnel Mine
  Tunnel -> Mine
    TIME_TICK
end
""")

    def test_hsm_name_must_be_identifier(self):
        with self.assertRaisesRegex(ModelError, "invalid participant name"):
            self.parse("""collab 1
hsm Bad-Name
ao Tunnel
collaboration Tunnel Bad-Name
  Tunnel -> Bad-Name
    TIME_TICK
end
""")


if __name__ == "__main__":
    unittest.main()
