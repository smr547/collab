"""Experimental reverse QM communication inventory.

Conservative source-pattern inventory. Findings are not completeness errors.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET

from qm_delivery import _blocks, _event_and_delivery, _timer_binding


@dataclass(frozen=True, order=True)
class Evidence:
    sender: str
    receiver: str
    signal: str
    mechanism: str


def discover_qm(root):
    """Return (routes, unresolved), each a set of evidence or descriptions."""
    classes = {n.get("name"): n for n in root.iter("class") if n.get("name")}
    subscribers = {}
    for name, node in classes.items():
        for _, code in _blocks(node):
            for sig in re.findall(r"\bsubscribe\s*\(\s*([A-Z][A-Z0-9_]*_SIG)\s*\)", code):
                subscribers.setdefault(sig, set()).add(name)

    routes, unresolved = set(), set()
    for name, node in classes.items():
        for _, code in _blocks(node):
            signals = set(re.findall(
                r"\bQ_NEW\s*\(\s*\w+\s*,\s*([A-Z][A-Z0-9_]*_SIG)\b", code))
            if len(signals) > 1:
                unresolved.add(f"{name}: multiple Q_NEW signals in one source block")
                continue
            for sig in signals:
                evidence = _event_and_delivery(code, sig)
                for mode, target in evidence:
                    if mode == "publish":
                        receivers = subscribers.get(sig, set())
                        if not receivers:
                            unresolved.add(f"{name}: publishes {sig}; no QM subscriber recognized")
                        for receiver in receivers:
                            routes.add(Evidence(name, receiver, sig[:-4], "publish/subscribe"))
                    elif mode == "post":
                        if target.startswith("AO_") and target[3:] in classes:
                            routes.add(Evidence(name, target[3:], sig[:-4], "direct POST"))
                        else:
                            unresolved.add(f"{name}: posts {sig} to {target}; target not resolved")
                if not evidence:
                    unresolved.add(f"{name}: constructs {sig}; delivery not recognized")
        for sig in set(re.findall(r"\bm_timeEvt\s*\(\s*this\s*,\s*([A-Z][A-Z0-9_]*_SIG)\s*,",
                                  "\n".join((item.findtext("code") or "") for item in node.iter("operation")))):
            if _timer_binding(node, sig):
                routes.add(Evidence(f"<timer:{name}>", name, sig[:-4], "QTimeEvt binding"))
    return routes, unresolved


def inspect_reverse(model, qm_path, aliases):
    root = ET.parse(qm_path).getroot()
    routes, unresolved = discover_qm(root)
    expected = set()
    for collab in model.collaborations:
        for flow in collab.flows:
            for sig in flow.signals:
                if model.roles.get(flow.sender) == "TIMER":
                    expected.add((f"<timer:{aliases.get(flow.receiver, flow.receiver)}>",
                                  aliases.get(flow.receiver, flow.receiver), sig))
                else:
                    expected.add((aliases.get(flow.sender, flow.sender),
                                  aliases.get(flow.receiver, flow.receiver), sig))
    covered = undeclared = 0
    for item in sorted(routes):
        status = "COVERED" if (item.sender, item.receiver, item.signal) in expected else "UNDECLARED"
        if status == "COVERED":
            covered += 1
        else:
            undeclared += 1
        print(f"{status}: QM {item.sender}->{item.receiver} {item.signal}: {item.mechanism}")
    for item in sorted(unresolved):
        print(f"UNRESOLVED: QM {item}")
    print(f"QM reverse inventory: {covered} covered, {undeclared} undeclared, "
          f"{len(unresolved)} unresolved; findings are advisory, not errors")
    return covered, undeclared, len(unresolved)
