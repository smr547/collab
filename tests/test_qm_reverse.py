"""Regression tests for reverse QM relationship discovery."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qm_reverse import Evidence, discover_qm


class ReverseTests(unittest.TestCase):
    def test_reverse_routes_and_extra_publisher(self):
        root = ET.fromstring("""<model>
<class name="Philo"><state><entry>
auto *e = Q_NEW(Evt, DONE_SIG); QP::QActive::PUBLISH(e, this);
</entry></state></class>
<class name="Table"><initial><action>subscribe(DONE_SIG);</action></initial>
<state><entry>auto *e = Q_NEW(Evt, TEST_SIG);
QP::QActive::PUBLISH(e, this);</entry></state></class>
</model>""")
        routes, unknown = discover_qm(root)
        self.assertIn(Evidence("Philo", "Table", "DONE", "publish/subscribe"), routes)
        self.assertIn("Table: publishes TEST_SIG; no QM subscriber recognized", unknown)

    def test_extra_subscriber_creates_distinct_route(self):
        root = ET.fromstring("""<model>
<class name="Philo"><state><entry>auto *e = Q_NEW(Evt, DONE_SIG);
QP::QActive::PUBLISH(e, this);</entry></state></class>
<class name="Table"><initial><action>subscribe(DONE_SIG);</action></initial></class>
<class name="Observer"><initial><action>subscribe(DONE_SIG);</action></initial></class>
</model>""")
        routes, _ = discover_qm(root)
        self.assertEqual({r.receiver for r in routes}, {"Table", "Observer"})

    def test_unrecognized_target_is_not_invented(self):
        root = ET.fromstring("""<model><class name="Philo">
<state><entry>auto *e = Q_NEW(Evt, HUNGRY_SIG);
AO_Unknown->POST(e, this);</entry></state></class></model>""")
        routes, unknown = discover_qm(root)
        self.assertFalse(routes)
        self.assertTrue(any("target not resolved" in s for s in unknown))


if __name__ == "__main__":
    unittest.main()
