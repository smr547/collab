"""Signal-level QM evidence independent of complete communication routes.

A subscription or transition trigger does not establish an event source.
"""
from __future__ import annotations

from collections import defaultdict
import re
import xml.etree.ElementTree as ET

from qm_delivery import _blocks


SIGNAL = r"([A-Z][A-Z0-9_]*_SIG)"
SUBSCRIBE = re.compile(r"\bsubscribe\s*\(\s*" + SIGNAL + r"\s*\)")
ALLOCATE = re.compile(r"\bQ_NEW\s*\(\s*\w+\s*,\s*" + SIGNAL + r"\b")
TIMER = re.compile(r"\bm_timeEvt\s*\(\s*this\s*,\s*" + SIGNAL + r"\s*,")
ENUM = re.compile(r"\b" + SIGNAL + r"\b")


def signal_inventory(root):
    """Return mapping signal -> categories -> QM class names.

    Categories are independently observed, not inferred communication edges.
    AppSignals enumeration is model-wide, hence marker '<model>'.
    """
    evidence = defaultdict(lambda: defaultdict(set))
    for attr in root.iter("attribute"):
        if attr.get("name") == "AppSignals":
            for sig in ENUM.findall(" ".join(attr.itertext())):
                evidence[sig]["declared"].add("<model>")
    for node in root.iter("class"):
        name = node.get("name")
        if not name:
            continue
        for _, code in _blocks(node):
            for sig in SUBSCRIBE.findall(code):
                evidence[sig]["subscribers"].add(name)
            for sig in ALLOCATE.findall(code):
                evidence[sig]["allocators"].add(name)
            for sig in TIMER.findall(code):
                evidence[sig]["timer_owners"].add(name)
        for tran in node.iter("tran"):
            trig = tran.get("trig", "")
            for bare in re.split(r"[\s,|]+", trig):
                if re.fullmatch(r"[A-Z][A-Z0-9_]*", bare):
                    sig = bare if bare.endswith("_SIG") else bare + "_SIG"
                    evidence[sig]["handlers"].add(name)
    return evidence


def inspect_signals(model, qm_path, aliases):
    evidence = signal_inventory(ET.parse(qm_path).getroot())
    contract = {sig + "_SIG" for collab in model.collaborations
                for flow in collab.flows for sig in flow.signals}
    print("QM signal evidence inventory (declarations/usages are not delivery routes):")
    for sig in sorted(evidence):
        kinds = evidence[sig]
        coverage = "DECLARED_IN_COLLAB" if sig in contract else "NOT_IN_COLLAB"
        parts = []
        for kind in ("declared", "allocators", "subscribers", "handlers", "timer_owners"):
            if kinds.get(kind):
                parts.append(f"{kind}={','.join(sorted(kinds[kind]))}")
        print(f"SIGNAL: {sig}: {coverage}; " + "; ".join(parts))
    print(f"QM signal inventory: {len(evidence)} signal(s), "
          f"{sum(sig not in contract for sig in evidence)} not in collaboration; "
          "no source or boundary inferred from subscriptions")
    return evidence
