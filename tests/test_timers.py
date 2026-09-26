"""Timer participants are event sources, not implicit Active Objects."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collabc import ModelError, generate_puml, generate_signals_hpp, parse_model


class TimerTests(unittest.TestCase):
    def parse(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timers.collab"
            path.write_text(content, encoding="utf-8")
            return parse_model(path)

    def test_timer_cadence_and_signal(self):
        model = self.parse('''collab 1
 ao Control
 timer SleepTimer "One-shot; inactivity interval"
 collaboration SleepTimer Control
   SleepTimer -> Control
     CONSIDER_SLEEPING
 end
''')
        self.assertEqual(model.roles["SleepTimer"], "TIMER")
        self.assertEqual(model.timer_cadences["SleepTimer"], "One-shot; inactivity interval")
        puml = generate_puml(model, "timers.collab")
        self.assertIn('component "◷ <b>SleepTimer</b>\\nOne-shot; inactivity interval" as SleepTimer <<TIMER>>', puml)
        self.assertIn("SleepTimer --> Control", puml)
        self.assertIn("CONSIDER_SLEEPING_SIG", generate_signals_hpp(model, "timers.collab", "AppSignals", "MAX_APP_SIG"))

    def test_timer_without_cadence(self):
        model = self.parse('''collab 1
 ao Control
 timer SleepTimer
 collaboration SleepTimer Control
   SleepTimer -> Control
     CONSIDER_SLEEPING
 end
''')
        self.assertNotIn("SleepTimer", model.timer_cadences)

    def test_duplicate_timer_name(self):
        with self.assertRaisesRegex(ModelError, "duplicate participant"):
            self.parse('collab 1\nao Control\ntimer Control\n')


if __name__ == "__main__":
    unittest.main()
