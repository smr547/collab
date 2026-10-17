"""External collaboration QM inspection: receiver evidence is not source evidence."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collabc import inspect_qm, parse_model
from qm_delivery import inspect_delivery

COLLAB = """collab 1
external User
ao Table
collaboration User Table
  User -> Table
    PAUSE
end
"""
QM = """<model>
<attribute name="AppSignals"><code>PAUSE_SIG</code></attribute>
<class name="Table"><state name="serving"><tran trig="PAUSE"/></state></class>
</model>"""


class ExternalQmTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.collab = Path(self.tmp.name) / "example.collab"
        self.qm = Path(self.tmp.name) / "example.qm"
        self.collab.write_text(COLLAB, encoding="utf-8")
        self.qm.write_text(QM, encoding="utf-8")
        self.model = parse_model(self.collab)

    def inspect(self, method):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = method(self.model, self.qm, {})
        return result, output.getvalue()

    def test_receiver_supported_without_external_qm_class(self):
        result, report = self.inspect(inspect_qm)
        self.assertEqual(result, (0, 0))
        self.assertIn("PARTIAL: User->Table PAUSE", report)
        self.assertIn("external origin and delivery not checked", report)
        self.assertNotIn("QM class identity unresolved: User", report)

    def test_external_delivery_remains_undetermined(self):
        result, report = self.inspect(inspect_delivery)
        self.assertEqual(result, (0, 1))
        self.assertIn("external origin/delivery", report)
        self.assertNotIn("QM sender identity unresolved", report)

    def test_missing_receiver_trigger_is_reported(self):
        self.qm.write_text(QM.replace('trig="PAUSE"', 'trig="OTHER"'))
        result, report = self.inspect(inspect_qm)
        self.assertEqual(result, (1, 0))
        self.assertIn("no PAUSE trigger", report)

    def test_missing_receiver_class_is_undetermined(self):
        self.qm.write_text(QM.replace('name="Table"', 'name="Elsewhere"'))
        result, report = self.inspect(inspect_qm)
        self.assertEqual(result, (0, 1))
        self.assertIn("QM receiver identity unresolved: Table", report)


if __name__ == "__main__":
    unittest.main()
