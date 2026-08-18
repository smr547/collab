import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "collabc.py"

spec = importlib.util.spec_from_file_location("collabc", MODULE_PATH)
collabc = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = collabc
spec.loader.exec_module(collabc)


def parse_source(text: str):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "model.collab"
        path.write_text(text, encoding="utf-8")
        return collabc.parse_model(path)


class SignalReuseTests(unittest.TestCase):
    def test_same_signal_two_sources_same_receiver_is_legal(self):
        model = parse_source("""\
collab 1
ao SourceOneAO
ao SourceTwoAO
ao ReceiverAO

collaboration SourceOneAO ReceiverAO
  SourceOneAO -> ReceiverAO
    EVENT_READY
end

collaboration SourceTwoAO ReceiverAO
  SourceTwoAO -> ReceiverAO
    EVENT_READY
end
""")
        self.assertEqual(
            list(collabc.unique_signals(model)),
            [("EVENT_READY", [("SourceOneAO", "ReceiverAO"),
                              ("SourceTwoAO", "ReceiverAO")])],
        )

    def test_reused_signal_generates_one_enum_member_and_all_routes(self):
        model = parse_source("""\
collab 1
ao SourceOneAO
ao SourceTwoAO
ao ReceiverAO

collaboration SourceOneAO ReceiverAO
  SourceOneAO -> ReceiverAO
    EVENT_READY
end

collaboration SourceTwoAO ReceiverAO
  SourceTwoAO -> ReceiverAO
    EVENT_READY
end
""")
        hpp = collabc.generate_signals_hpp(
            model, "model.collab", "AppSignals", "MAX_APP_SIG")
        self.assertEqual(hpp.count("EVENT_READY_SIG"), 1)
        self.assertIn("//   SourceOneAO -> ReceiverAO", hpp)
        self.assertIn("//   SourceTwoAO -> ReceiverAO", hpp)

    def test_same_signal_different_receiver_is_rejected(self):
        source = """\
collab 1
ao SourceOneAO
ao SourceTwoAO
ao ReceiverOneAO
ao ReceiverTwoAO

collaboration SourceOneAO ReceiverOneAO
  SourceOneAO -> ReceiverOneAO
    EVENT_READY
end

collaboration SourceTwoAO ReceiverTwoAO
  SourceTwoAO -> ReceiverTwoAO
    EVENT_READY
end
"""
        with self.assertRaises(collabc.ModelError) as ctx:
            parse_source(source)
        msg = str(ctx.exception)
        self.assertIn("EVENT_READY", msg)
        self.assertIn("ReceiverOneAO", msg)
        self.assertIn("ReceiverTwoAO", msg)

    def test_duplicate_signal_in_same_flow_is_rejected(self):
        source = """\
collab 1
ao SourceAO
ao ReceiverAO

collaboration SourceAO ReceiverAO
  SourceAO -> ReceiverAO
    EVENT_READY
    EVENT_READY
end
"""
        with self.assertRaises(collabc.ModelError) as ctx:
            parse_source(source)
        self.assertIn("duplicate signal 'EVENT_READY' in flow", str(ctx.exception))

    def test_unique_signal_order_is_first_seen_order(self):
        model = parse_source("""\
collab 1
ao SourceOneAO
ao SourceTwoAO
ao ReceiverAO

collaboration SourceOneAO ReceiverAO
  SourceOneAO -> ReceiverAO
    FIRST
    SECOND
end

collaboration SourceTwoAO ReceiverAO
  SourceTwoAO -> ReceiverAO
    FIRST
    THIRD
end
""")
        self.assertEqual(
            [sig for sig, _routes in collabc.unique_signals(model)],
            ["FIRST", "SECOND", "THIRD"],
        )

    def test_plantuml_still_shows_signal_on_each_route(self):
        model = parse_source("""\
collab 1
ao SourceOneAO
ao SourceTwoAO
ao ReceiverAO

collaboration SourceOneAO ReceiverAO
  SourceOneAO -> ReceiverAO
    EVENT_READY
end

collaboration SourceTwoAO ReceiverAO
  SourceTwoAO -> ReceiverAO
    EVENT_READY
end
""")
        puml = collabc.generate_puml(model, "model.collab")
        self.assertEqual(puml.count("EVENT_READY"), 2)


if __name__ == "__main__":
    unittest.main()
