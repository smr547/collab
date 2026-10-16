"""Experimental QM delivery inspection for QP/C++ DPP-style models.

This is source-pattern evidence, not a C++ compiler, control-flow analysis,
or proof of runtime delivery. Unknown patterns must remain undetermined.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET


def _blocks(node):
    """QM actions may be text in entry/exit/tran/choice, or child <code>."""
    for item in node.iter():
        if item.tag in ("code", "entry", "exit", "tran", "choice", "initial", "operation"):
            source = item.text or ""
            if source.strip():
                yield item.tag, source


def _event_and_delivery(source, signal):
    """Recognize a locally constructed Q_NEW event and its delivery call.

    Deliberately conservative: do not match arbitrary mentions of a signal.
    A block with multiple different event signals is ambiguous.
    """
    allocated = set(re.findall(r"\bQ_NEW\s*\(\s*\w+\s*,\s*([A-Z][A-Z0-9_]*_SIG)\b", source))
    if allocated != {signal}:
        return set()
    modes = set()
    if re.search(r"\b(?:\w+::)*PUBLISH\s*\(", source):
        modes.add(("publish", None))
    for target in re.findall(r"\b(\w+)\s*->\s*POST\s*\(", source):
        modes.add(("post", target))
    return modes


def _subscriptions(node, signal):
    return any(re.search(r"\bsubscribe\s*\(\s*" + re.escape(signal) + r"\s*\)", source)
               for _, source in _blocks(node))


def _timer_binding(node, signal):
    # A QM constructor binds a QTimeEvt to 'this' and a signal.
    for item in node.iter("operation"):
        source = item.findtext("code") or ""
        if re.search(r"\bm_timeEvt\s*\(\s*this\s*,\s*" + re.escape(signal) + r"\s*,", source):
            return True
    return False


def inspect_delivery(model, qm_path, aliases):
    """Print one evidence-based classification per declared edge.

    Return (missing, undetermined). MISSING is reserved for explicit negative
    evidence, not mere absence of a recognized C++ source pattern.
    """
    root = ET.parse(qm_path).getroot()
    classes = {node.get("name"): node for node in root.iter("class") if node.get("name")}
    missing = 0
    unknown = 0
    for collab in model.collaborations:
        for flow in collab.flows:
            sender, receiver = flow.sender, flow.receiver
            source_name = aliases.get(sender, sender)
            target_name = aliases.get(receiver, receiver)
            for sig in flow.signals:
                token = sig + "_SIG"
                prefix = f"{sender}->{receiver} {sig}"
                target = classes.get(target_name)
                if target is None:
                    print(f"UNDETERMINED: {prefix}: QM receiver identity unresolved")
                    unknown += 1
                    continue
                if model.roles.get(sender) == "TIMER":
                    if _timer_binding(target, token):
                        print(f"SUPPORTED: {prefix}: QM QTimeEvt binds {token} to this "
                              "(timer arm and runtime firing not proven)")
                    else:
                        print(f"UNDETERMINED: {prefix}: no recognized QTimeEvt binding")
                        unknown += 1
                    continue
                source = classes.get(source_name)
                if source is None:
                    print(f"UNDETERMINED: {prefix}: QM sender identity unresolved")
                    unknown += 1
                    continue
                evidence = set()
                for _, code in _blocks(source):
                    evidence.update(_event_and_delivery(code, token))
                direct = ("post", "AO_" + target_name) in evidence
                published = ("publish", None) in evidence
                subscribed = _subscriptions(target, token)
                if direct:
                    print(f"SUPPORTED: {prefix}: Q_NEW({token}) and "
                          f"AO_{target_name}->POST in QM sender")
                elif published and subscribed:
                    print(f"SUPPORTED: {prefix}: Q_NEW({token}) and PUBLISH in "
                          f"{source_name}; subscribe({token}) in {target_name}")
                elif published and not subscribed:
                    print(f"UNDETERMINED: {prefix}: publication recognized, "
                          f"but no subscribe({token}) recognized in receiver")
                    unknown += 1
                else:
                    print(f"UNDETERMINED: {prefix}: delivery mechanism not recognized")
                    unknown += 1
    print(f"QM delivery inspection: {missing} missing, {unknown} undetermined; "
          "SUPPORTED means source-pattern evidence, not runtime proof")
    return missing, unknown
