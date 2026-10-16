"""Focused tests for the conservative QM inspection pass.

Run: python3 -m unittest discover -s tests -p 'test_qm_inspection.py'
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "collabc.py"
spec = importlib.util.spec_from_file_location("collabc", SOURCE)
collabc = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = collabc
spec.loader.exec_module(collabc)

COLLAB = """collab 1
ao Philosopher
ao Table
timer Tick
collaboration Philosopher Table
  Philosopher -> Table
    HUNGRY
end
collaboration Tick Philosopher
  Tick -> Philosopher
    TIMEOUT
end
"""
QM = """<model>
<attribute name="AppSignals" type="enum"><code>HUNGRY_SIG, TIMEOUT_SIG</code></attribute>
<class name="Philo"><state name="thinking"><tran trig="TIMEOUT"/></state></class>
<class name="Table"><state name="serving"><tran trig="HUNGRY"/></state></class>
</model>"""


class QmInspectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "sample.collab").write_text(COLLAB)
        (self.base / "sample.qm").write_text(QM)
        self.model = collabc.parse_model(self.base / "sample.collab")

    def test_alias_and_receiver_trigger(self):
        self.assertEqual(collabc.inspect_qm(self.model, self.base / "sample.qm",
                                           {"Philosopher": "Philo"}), (0, 1))

    def test_unresolved_alias_is_not_a_false_failure(self):
        self.assertEqual(collabc.inspect_qm(self.model, self.base / "sample.qm",
                                           {}), (0, 2))

    def test_missing_receiver_trigger(self):
        (self.base / "sample.qm").write_text(QM.replace('trig="HUNGRY"', 'trig="DONE"'))
        self.assertEqual(collabc.inspect_qm(self.model, self.base / "sample.qm",
                                           {"Philosopher": "Philo"}), (1, 1))

    def test_duplicate_alias_rejected(self):
        with self.assertRaises(collabc.ModelError):
            collabc.parse_qm_aliases(["Philosopher=Philo", "Philosopher=Other"])


if __name__ == "__main__":
    unittest.main()
