"""Tests for signal evidence that has no complete route."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qm_signals import signal_inventory


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
