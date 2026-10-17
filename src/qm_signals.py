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
ENUM_SENTINELS = {"Q_USER_SIG", "MAX_PUB_SIG", "MAX_SIG"}


def declared_signals(root):
    """Find signal enumerators in supported QM model declarations.

    Legacy AppSignals attributes can contain an enumerator fragment rather than
    a complete C++ enum. File templates must contain an actual enum definition;
    references in comments, actions, and other template text do not declare signals.
    """
    declared = set()
    for attr in root.iter("attribute"):
        if attr.get("name") == "AppSignals":
            source = attr.findtext("code") or ""
            # Preserve the historical QM AppSignals attribute convention.
            declared.update(ENUM.findall(source))

    for file_node in root.iter("file"):
        for text_node in file_node.findall("text"):
            source = "".join(text_node.itertext())
            source = re.sub(r"/\\*.*?\\*/|//[^\\n]*", "", source, flags=re.S)
            for match in re.finditer(
                r"\\benum\\s+[A-Za-z_]\\w*\\s*(?::\\s*[^{};]+)?\\s*\\{([^{}]*)\\}",
                source, flags=re.S,
            ):
                for entry in match.group(1).split(","):
                    entry = entry.strip()
                    identifier = re.match(r"([A-Za-z_]\\w*)\\s*(?:=|$)", entry)
                    if identifier and identifier.group(1).endswith("_SIG"):
                        declared.add(identifier.group(1))
    return declared - ENUM_SENTINELS


def signal_inventory(root):
    """Return mapping signal -> categories -> QM class names.

    Categories are independently observed, not inferred communication edges.
    AppSignals enumeration is model-wide, hence marker '<model>'.
    """
    evidence = defaultdict(lambda: defaultdict(set))
    for sig in declared_signals(root):
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
    absent = sorted(sig for sig in evidence if sig not in contract)
    print(f"QM application-signal inventory: {len(evidence)} signal(s); "
          f"{len(evidence) - len(absent)} represented in collaboration; "
          f"{len(absent)} not represented ({', '.join(absent) or 'none'}); "
          "these are signal identities, not additional proven routes")
    return evidence
