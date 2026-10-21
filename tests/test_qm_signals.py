"""Tests for signal evidence that has no complete route."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qm_signals import signal_inventory, declared_signals
from collabc import Model, Collaboration, Flow, inspect_qm
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from io import StringIO


class SignalEvidenceTests(unittest.TestCase):
    def test_declaration_subscriptions_and_triggers_without_publishers(self):
        root = ET.fromstring("""<model>
<attribute name="AppSignals"><code>Q_USER_SIG, PAUSE_SIG, SERVE_SIG, TEST_SIG, DONE_SIG, MAX_PUB_SIG, MAX_SIG</code></attribute>
<class name="Philo"><initial><action>subscribe(TEST_SIG);</action></initial>
<state><tran trig="TEST"/></state></class>
<class name="Table"><initial><action>
subscribe(PAUSE_SIG); subscribe(SERVE_SIG); subscribe(TEST_SIG);
</action></initial><state><tran trig="PAUSE"/><tran trig="SERVE"/></state></class>
</model>""")
        evidence = signal_inventory(root)
        self.assertEqual(evidence["TEST_SIG"]["subscribers"], {"Philo", "Table"})
        self.assertEqual(evidence["PAUSE_SIG"]["subscribers"], {"Table"})
        self.assertEqual(evidence["SERVE_SIG"]["handlers"], {"Table"})
        self.assertEqual(evidence["DONE_SIG"]["declared"], {"<model>"})
        self.assertNotIn("allocators", evidence["TEST_SIG"])
        for sentinel in ("Q_USER_SIG", "MAX_PUB_SIG", "MAX_SIG"):
            self.assertNotIn(sentinel, evidence)

    def test_header_template_enum_is_a_declaration_not_a_reference(self):
        root = ET.fromstring("""<model>
<directory name="."><file name="game.hpp"><text>
#ifndef GAME_HPP_
enum GameSignals : QP::QSignal {
 TIME_TICK_SIG = QP::Q_USER_SIG, // first
 PLAYER_TRIGGER_SIG, /* event */
 MAX_PUB_SIG,
 MISSILE_FIRE_SIG,
 HIT_MINE_SIG,
 MAX_SIG
};
// FAKE_COMMENT_SIG
void f() { use(FAKE_CODE_SIG); }
</text></file></directory>
<class name="Ship"><state><tran trig="HIT_MINE"/></state></class>
</model>""")
        self.assertEqual(declared_signals(root),
                         {"TIME_TICK_SIG", "PLAYER_TRIGGER_SIG",
                          "MISSILE_FIRE_SIG", "HIT_MINE_SIG"})
        evidence = signal_inventory(root)
        self.assertEqual(evidence["HIT_MINE_SIG"]["declared"], {"<model>"})
        self.assertNotIn("FAKE_COMMENT_SIG", evidence)
        self.assertNotIn("FAKE_CODE_SIG", evidence)

    def test_forward_inspection_uses_header_template_declarations(self):
        xml = """<model>
<directory><file name="game.hpp"><text>
enum GameSignals : QP::QSignal { HIT_MINE_SIG, MAX_SIG };
</text></file></directory>
<class name="Mine1"/>
<class name="Ship"><state><tran trig="HIT_MINE"/></state></class>
</model>"""
        model = Model(aos=["Mine1", "Ship"],
                      roles={"Mine1": "AO", "Ship": "AO"},
                      collaborations=[Collaboration(
                          "Mine1", "Ship",
                          [Flow("Mine1", "Ship", ["HIT_MINE"])])])
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "game.qm"
            path.write_text(xml)
            output = StringIO()
            with redirect_stdout(output):
                missing, unknown = inspect_qm(model, path, {})
        self.assertEqual((missing, unknown), (0, 0))
        self.assertIn("PARTIAL: Mine1->Ship HIT_MINE", output.getvalue())

    def test_appsignals_attribute_still_supported(self):
        root = ET.fromstring("""<model>
<attribute name="AppSignals"><code>
Q_USER_SIG, PAUSE_SIG, SERVE_SIG, MAX_SIG
</code></attribute></model>""")
        self.assertEqual(declared_signals(root), {"PAUSE_SIG", "SERVE_SIG"})

    def test_allocation_and_timer_are_separate_facts(self):
        root = ET.fromstring("""<model><class name="Philo">
<operation name="Philo"><code>m_timeEvt(this, TIMEOUT_SIG, 0U)</code></operation>
<state><entry>auto *e = Q_NEW(Evt, DONE_SIG);</entry></state>
</class></model>""")
        evidence = signal_inventory(root)
        self.assertEqual(evidence["DONE_SIG"]["allocators"], {"Philo"})
        self.assertEqual(evidence["TIMEOUT_SIG"]["timer_owners"], {"Philo"})


if __name__ == "__main__":
    unittest.main()
