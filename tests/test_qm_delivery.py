"""Source-pattern tests for experimental QM delivery inspection."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from qm_delivery import _event_and_delivery, _subscriptions, _timer_binding, inspect_delivery
from collabc import parse_model


class DeliveryTests(unittest.TestCase):
    def test_post(self):
        code = "auto *pe = Q_NEW(TableEvt, HUNGRY_SIG);\nAO_Table->POST(pe, this);"
        self.assertIn(("post", "AO_Table"), _event_and_delivery(code, "HUNGRY_SIG"))

    def test_publish(self):
        code = "auto *pe = Q_NEW(TableEvt, DONE_SIG);\nQP::QActive::PUBLISH(pe, this);"
        self.assertIn(("publish", None), _event_and_delivery(code, "DONE_SIG"))

    def test_unrelated_signal_not_attributed(self):
        code = "auto *pe = Q_NEW(TableEvt, EAT_SIG);\nQP::QActive::PUBLISH(pe, this);"
        self.assertEqual(_event_and_delivery(code, "DONE_SIG"), set())

    def test_ambiguous_allocations_remain_unknown(self):
        code = ("Q_NEW(TableEvt, EAT_SIG); Q_NEW(TableEvt, DONE_SIG); "
                "QP::QActive::PUBLISH(pe, this);")
        self.assertEqual(_event_and_delivery(code, "DONE_SIG"), set())

    def test_dpp_style_xml(self):
        collab = """collab 1
ao Philosopher
ao Table
timer PhilosopherTimer
collaboration Philosopher Table
  Philosopher -> Table
    HUNGRY
    DONE
  Table -> Philosopher
    EAT
end
collaboration PhilosopherTimer Philosopher
  PhilosopherTimer -> Philosopher
    TIMEOUT
end
"""
        qm = """<model>
<class name="Philo">
<operation name="Philo"><code>: m_timeEvt(this, TIMEOUT_SIG, 0U)</code></operation>
<initial><action>subscribe(EAT_SIG);</action></initial>
<state><entry>auto *pe = Q_NEW(TableEvt, HUNGRY_SIG);
AO_Table->POST(pe, this);</entry>
<exit>auto *pe = Q_NEW(TableEvt, DONE_SIG);
QP::QActive::PUBLISH(pe, this);</exit></state>
</class>
<class name="Table">
<initial><action>subscribe(DONE_SIG);</action></initial>
<state><entry>auto *pe = Q_NEW(TableEvt, EAT_SIG);
QP::QActive::PUBLISH(pe, this);</entry></state>
</class>
</model>"""
        with tempfile.TemporaryDirectory() as d:
            cp, qp = Path(d) / "d.collab", Path(d) / "d.qm"
            cp.write_text(collab)
            qp.write_text(qm)
            self.assertEqual(inspect_delivery(parse_model(cp), qp, {"Philosopher": "Philo"}),
                             (0, 0))


if __name__ == "__main__":
    unittest.main()
