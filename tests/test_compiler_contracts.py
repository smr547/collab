"""Additional compiler contract tests: invalid input, signal identity and DPP."""
import tempfile
import unittest
from pathlib import Path

from test_compiler_regression import collabc, ROOT

DPP = ROOT / "examples" / "DPP.collab"


class ParserContractTests(unittest.TestCase):
    def parse_text(self, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.collab"
            path.write_text(source, encoding="utf-8")
            return collabc.parse_model(path)

    def assert_invalid(self, source, message):
        with self.assertRaisesRegex(collabc.ModelError, message):
            self.parse_text(source)

    def test_unsupported_version(self):
        self.assert_invalid("collab 2\nao A\nao B\ncollaboration A B\n A -> B\n  READY\nend\n", "unsupported")

    def test_duplicate_participant(self):
        self.assert_invalid("collab 1\nao A\nao A\n", "duplicate participant")

    def test_undeclared_endpoint(self):
        self.assert_invalid("collab 1\nao A\ncollaboration A B\n", "has not been declared")

    def test_duplicate_collaboration_reversed(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\n  READY\nend\n"
            "collaboration B A\n B -> A\n  ACK\nend\n",
            "duplicate collaboration",
        )

    def test_flow_endpoint_mismatch(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\nao C\ncollaboration A B\n A -> C\n  READY\nend\n",
            "does not match",
        )

    def test_duplicate_direction(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\n  READY\n A -> B\n  ACK\nend\n",
            "duplicate direction",
        )

    def test_duplicate_signal_in_flow(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\n  READY\n  READY\nend\n",
            "duplicate signal",
        )

    def test_missing_end(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\n  READY\n",
            "missing 'end'",
        )

    def test_empty_flow(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\nend\n",
            "contains no signals",
        )

    def test_invalid_signal_case(self):
        self.assert_invalid(
            "collab 1\nao A\nao B\ncollaboration A B\n A -> B\n  Ready\nend\n",
            "invalid signal name",
        )

    def test_repeated_signal_has_single_enum_identity(self):
        model = self.parse_text(
            "collab 1\nao A\nao B\nao C\n"
            "collaboration A B\n A -> B\n  TICK\nend\n"
            "collaboration A C\n A -> C\n  TICK\nend\n"
        )
        self.assertEqual(
            list(collabc.unique_signals(model)),
            [("TICK", [("A", "B"), ("A", "C")])],
        )
        header = collabc.generate_signals_hpp(model, "case.collab", "AppSignals", "MAX_APP_SIG")
        self.assertEqual(header.count("TICK_SIG"), 1)
        self.assertIn("A -> B", header)
        self.assertIn("A -> C", header)


class DPPRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = collabc.parse_model(DPP)
        cls.puml = collabc.generate_puml(cls.model, DPP.name)

    def test_model_counts_and_roles(self):
        self.assertEqual(len(self.model.aos), 4)
        self.assertEqual(len(self.model.collaborations), 3)
        self.assertEqual(len(list(collabc.unique_signals(self.model))), 6)
        self.assertEqual(self.model.roles["PhilosopherTimer"], "TIMER")
        self.assertEqual(self.model.roles["User"], "EXTERNAL")

    def test_bidirectional_table_philosopher(self):
        self.assertIn("Philosopher <--> Table", self.puml)
        self.assertIn("<b>-> Table</b>", self.puml)
        self.assertIn("<b>-> Philosopher</b>", self.puml)
        for signal in ("HUNGRY", "DONE", "EAT"):
            self.assertIn(signal, self.puml)

    def test_single_timer_and_legend(self):
        self.assertEqual(self.puml.count('usecase "<b>T</b>'), 1)
        self.assertIn("PhilosopherTimer -right-> Philosopher", self.puml)
        self.assertIn("One-shot; thinking and eating random interval", self.puml)
        self.assertIn("TIMEOUT", self.puml)
        self.assertIn("legend bottom", self.puml)

    def test_external_actor_and_unidirectional_signals(self):
        self.assertIn('actor "User" as User', self.puml)
        self.assertIn("User --> Table", self.puml)
        self.assertIn("  PAUSE", self.puml)
        self.assertIn("  SERVE", self.puml)


if __name__ == "__main__":
    unittest.main()
