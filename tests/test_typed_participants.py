"""Typed participant regression tests. Run: python3 -m unittest discover -s tests -v"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("collabc", Path(__file__).resolve().parents[1] / "src" / "collabc.py")
collabc = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = collabc
SPEC.loader.exec_module(collabc)

class TypedParticipantsTests(unittest.TestCase):
    def parse(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.collab"
            path.write_text(source, encoding="utf-8")
            return collabc.parse_model(path)

    def test_ao_and_isr_stereotypes_and_no_suffix_warning(self):
        model = self.parse("""collab 1
ao TippingBucket
isr BucketReedSwitch
collaboration BucketReedSwitch TippingBucket
  BucketReedSwitch -> TippingBucket
    BUCKET_SWITCH_CLOSING
end
""")
        self.assertEqual(model.roles, {"TippingBucket": "AO", "BucketReedSwitch": "ISR"})
        self.assertEqual(model.warnings, [])
        puml = collabc.generate_puml(model, "sample.collab")
        self.assertIn('component "TippingBucket" as TippingBucket <<AO>>', puml)
        self.assertIn('component "BucketReedSwitch" as BucketReedSwitch <<ISR>>', puml)
        self.assertIn("BUCKET_SWITCH_CLOSING_SIG", collabc.generate_signals_hpp(model, "sample.collab", "AppSignals", "MAX_APP_SIG"))

    def test_legacy_ao_suffix_remains_valid(self):
        model = self.parse("""collab 1
ao BucketSensorAO
ao ControlAO
collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
end
""")
        self.assertEqual(len(model.collaborations), 1)
        self.assertEqual(model.warnings, [])

    def test_duplicate_name_across_roles_is_rejected(self):
        with self.assertRaisesRegex(collabc.ModelError, "duplicate AO"):
            self.parse("""collab 1
ao TippingBucket
isr TippingBucket
collaboration TippingBucket Control
end
""")

if __name__ == "__main__":
    unittest.main()
