#!/usr/bin/env python3
"""
collabc.py -- compile a .collab Active Object collaboration model.

Input:
    human-readable .collab DSL

Outputs:
    <stem>.puml          PlantUML collaboration diagram
    <stem>-signals.hpp   QP-compatible C++ signal enum

The .collab file is authoritative. PlantUML arrowheads and C++ signal
declarations are derived from the directional signal groups.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


AO_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SIGNAL_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
FLOW_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\s*$"
)

GENERIC_STATUS_SIGNALS = {
    "SENSOR_BUSY",
    "SENSOR_IDLE",
    "SENSOR_FAULT",
}


class ModelError(Exception):
    pass


@dataclass
class Flow:
    sender: str
    receiver: str
    signals: List[str] = field(default_factory=list)
    line_no: int = 0


@dataclass
class Collaboration:
    a: str
    b: str
    flows: List[Flow] = field(default_factory=list)
    line_no: int = 0

    @property
    def pair_key(self) -> Tuple[str, str]:
        return tuple(sorted((self.a, self.b)))


@dataclass
class Model:
    version: int = 1
    title: str = "AO Collaboration"
    aos: List[str] = field(default_factory=list)
    roles: dict[str, str] = field(default_factory=dict)
    timer_cadences: dict[str, str] = field(default_factory=dict)
    collaborations: List[Collaboration] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def strip_comment(line: str) -> str:
    # '#' starts a comment unless inside a quoted string.
    in_quote = False
    escaped = False
    out = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_quote = not in_quote
            out.append(ch)
            continue
        if ch == "#" and not in_quote:
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_model(path: Path) -> Model:
    model = Model()
    current_collab: Collaboration | None = None
    current_flow: Flow | None = None

    seen_aos = set()
    seen_pairs = set()
    # Signal identity is global; each flow separately rejects duplicate entries.

    lines = path.read_text(encoding="utf-8").splitlines()

    for idx, raw in enumerate(lines, start=1):
        line = strip_comment(raw)
        if not line.strip():
            continue

        stripped = line.strip()

        if current_collab is None:
            if stripped.startswith("collab "):
                parts = stripped.split()
                if len(parts) != 2 or not parts[1].isdigit():
                    raise ModelError(f"{path}:{idx}: expected 'collab <integer-version>'")
                model.version = int(parts[1])
                if model.version != 1:
                    raise ModelError(
                        f"{path}:{idx}: unsupported .collab version {model.version}; "
                        "this compiler supports version 1"
                    )
                continue

            if stripped.startswith("title "):
                try:
                    parts = shlex.split(stripped)
                except ValueError as exc:
                    raise ModelError(f"{path}:{idx}: invalid title: {exc}") from exc
                if len(parts) < 2:
                    raise ModelError(f"{path}:{idx}: title requires text")
                model.title = " ".join(parts[1:])
                continue

            if stripped.startswith(("ao ", "hsm ", "isr ", "external ", "timer ")):
                if stripped.startswith("timer "):
                    try:
                        parts = shlex.split(stripped)
                    except ValueError as exc:
                        raise ModelError(f"{path}:{idx}: invalid timer declaration: {exc}") from exc
                    if len(parts) not in (2, 3):
                        raise ModelError(f"{path}:{idx}: expected timer name and optional quoted cadence")
                    name = parts[1]
                    if not AO_RE.match(name):
                        raise ModelError(f"{path}:{idx}: invalid participant name '{name}'")
                    if name in seen_aos:
                        raise ModelError(f"{path}:{idx}: duplicate participant '{name}'")
                    seen_aos.add(name)
                    model.aos.append(name)
                    model.roles[name] = "TIMER"
                    if len(parts) == 3:
                        model.timer_cadences[name] = parts[2]
                    continue
                parts = stripped.split()
                if len(parts) != 2:
                    raise ModelError(f"{path}:{idx}: expected 'ao <Name>', 'hsm <Name>', 'isr <Name>' or 'external <Name>'")
                role = parts[0].upper()
                name = parts[1]
                if not AO_RE.match(name):
                    raise ModelError(f"{path}:{idx}: invalid participant name '{name}'")
                if name in seen_aos:
                    raise ModelError(f"{path}:{idx}: duplicate participant '{name}'")
                seen_aos.add(name)
                model.aos.append(name)
                model.roles[name] = role
                continue

            if stripped.startswith("collaboration "):
                parts = stripped.split()
                if len(parts) != 3:
                    raise ModelError(
                        f"{path}:{idx}: expected "
                        "'collaboration <Participant1> <Participant2>'"
                    )
                a, b = parts[1], parts[2]
                if a == b:
                    raise ModelError(
                        f"{path}:{idx}: collaboration endpoints must differ"
                    )
                for name in (a, b):
                    if name not in seen_aos:
                        raise ModelError(
                            f"{path}:{idx}: participant '{name}' has not been declared"
                        )
                pair = tuple(sorted((a, b)))
                if pair in seen_pairs:
                    raise ModelError(
                        f"{path}:{idx}: duplicate collaboration between {a} and {b}"
                    )
                seen_pairs.add(pair)
                current_collab = Collaboration(a=a, b=b, line_no=idx)
                current_flow = None
                continue

            raise ModelError(
                f"{path}:{idx}: unexpected statement outside collaboration: "
                f"{stripped!r}"
            )

        # Inside a collaboration
        if stripped == "end":
            if not current_collab.flows:
                raise ModelError(
                    f"{path}:{current_collab.line_no}: collaboration "
                    f"{current_collab.a}/{current_collab.b} contains no signal flows"
                )
            for flow in current_collab.flows:
                if not flow.signals:
                    raise ModelError(
                        f"{path}:{flow.line_no}: flow "
                        f"{flow.sender}->{flow.receiver} contains no signals"
                    )
            model.collaborations.append(current_collab)
            current_collab = None
            current_flow = None
            continue

        m = FLOW_RE.match(line)
        if m:
            sender, receiver = m.groups()
            endpoints = {current_collab.a, current_collab.b}
            if {sender, receiver} != endpoints:
                raise ModelError(
                    f"{path}:{idx}: flow {sender}->{receiver} does not match "
                    f"collaboration {current_collab.a}/{current_collab.b}"
                )
            if any(
                f.sender == sender and f.receiver == receiver
                for f in current_collab.flows
            ):
                raise ModelError(
                    f"{path}:{idx}: duplicate direction block "
                    f"{sender}->{receiver}; group signals together"
                )
            current_flow = Flow(
                sender=sender,
                receiver=receiver,
                line_no=idx,
            )
            current_collab.flows.append(current_flow)
            continue

        # A signal must be indented under a directional flow.
        if current_flow is None:
            raise ModelError(
                f"{path}:{idx}: expected a directional flow "
                "'AO1 -> AO2' or 'end'"
            )

        signal = stripped
        if not SIGNAL_RE.match(signal):
            raise ModelError(
                f"{path}:{idx}: invalid signal name '{signal}'; "
                "use UPPER_SNAKE_CASE"
            )
        if signal in current_flow.signals:
            raise ModelError(
                f"{path}:{idx}: duplicate signal '{signal}' in flow "
                f"{current_flow.sender}->{current_flow.receiver}"
            )

        current_flow.signals.append(signal)

        if signal in GENERIC_STATUS_SIGNALS:
            model.warnings.append(
                f"{path}:{idx}: generic status signal '{signal}' obscures "
                "the sender identity; prefer a sender/domain-specific name"
            )

    if current_collab is not None:
        raise ModelError(
            f"{path}:{current_collab.line_no}: collaboration "
            f"{current_collab.a}/{current_collab.b} is missing 'end'"
        )

    if not model.aos:
        raise ModelError(f"{path}: no participants declared")
    if not model.collaborations:
        raise ModelError(f"{path}: no collaborations declared")

    return model


def puml_arrow(collab: Collaboration) -> str:
    a_to_b = any(f.sender == collab.a and f.receiver == collab.b for f in collab.flows)
    b_to_a = any(f.sender == collab.b and f.receiver == collab.a for f in collab.flows)

    if a_to_b and b_to_a:
        return "<-->"
    if a_to_b:
        return "-->"
    if b_to_a:
        return "<--"
    raise AssertionError("validated collaboration must contain at least one flow")


def generate_puml(model: Model, source_name: str) -> str:
    """Render a compact collaboration diagram with local timer occurrences.

    A timer remains one semantic participant, even when drawn beside multiple
    recipients. Timer details live in the legend; directed non-timer links
    need only their signal names. Bidirectional links name each receiver.
    """
    out = [
        "@startuml",
        f"' GENERATED from {source_name}; do not edit by hand.",
        "' Timer aliases are graphical occurrences of one logical participant.",
        f"title {model.title}",
        "skinparam linetype polyline",
        "skinparam shadowing false",
        "top to bottom direction",
        "skinparam usecase {",
        "  BackgroundColor White",
        "  BorderColor #666666",
        "}",
    ]

    timer_links = [c for c in model.collaborations
                   if model.roles.get(c.a) == "TIMER"
                   or model.roles.get(c.b) == "TIMER"]
    ordinary_links = [c for c in model.collaborations if c not in timer_links]

    # Declare participants in the same role-group order as the J experiment.
    for name in model.aos:
        if model.roles.get(name) == "EXTERNAL":
            out.append(f'actor "{name}" as {name}')

    timer_occurrences = []
    timer_names = [name for name in model.aos if model.roles.get(name) == "TIMER"]
    # Shared periodic timers first, then local one-shot timers.
    timer_names.sort(key=lambda name: -sum(name in (c.a, c.b) for c in timer_links))
    for name in timer_names:
        links = [c for c in timer_links if name in (c.a, c.b)]
        for c in links:
            receiver = c.b if c.a == name else c.a
            alias = f"{name}__{receiver}" if len(links) > 1 else name
            label = f"<b>T</b>\\n<size:9>{name}:</size>"
            out.append(f'usecase "{label}" as {alias}')
            timer_occurrences.append((name, receiver, alias, c))

    for name in model.aos:
        role = model.roles.get(name, "AO")
        if role in ("EXTERNAL", "TIMER"):
            continue
        label = f"<size:17><b>{name}</b></size>" if role == "AO" else name
        out.append(f'component "{label}" as {name} <<{role}>>')

    if timer_occurrences:
        out.extend(["", "legend bottom", "  |= Timer |= Behaviour |= Signal posted |"])
        seen = set()
        for name, _receiver, _alias, c in timer_occurrences:
            if name in seen:
                continue
            seen.add(name)
            cadence = (model.timer_cadences.get(name, "")\n                       .replace("&", "&amp;")\n                       .replace("<", "&lt;")\n                       .replace(">", "&gt;"))
            signals = list(dict.fromkeys(sig for link in timer_links
                                          if name in (link.a, link.b)
                                          for flow in link.flows
                                          if flow.sender == name
                                          for sig in flow.signals))
            out.append(f"  | <b>T</b> {name} | {cadence} | {', '.join(signals)} |")
        out.append("endlegend")

    out.append("")
    for name, receiver, alias, c in timer_occurrences:
        flow = c.flows[0]
        if flow.sender == name:
            out.append(f"{alias} -right-> {receiver}")
        else:
            out.append(f"{receiver} -left-> {alias}")

    out.append("")
    for collab in ordinary_links:
        out.append(f"{collab.a} {puml_arrow(collab)} {collab.b}")
        out.append("note on link")
        if len(collab.flows) == 1:
            for signal in collab.flows[0].signals:
                out.append(f"  {signal}")
        else:
            for flow in collab.flows:
                out.append(f"  <b>-> {flow.receiver}</b>")
                for signal in flow.signals:
                    out.append(f"    {signal}")
        out.append("end note")

    out.extend(["@enduml", ""])
    return "\n".join(out)

def all_signals(model: Model):
    for collab in model.collaborations:
        for flow in collab.flows:
            for sig in flow.signals:
                yield sig, flow.sender, flow.receiver


def unique_signals(model: Model):
    """Yield each semantic signal once, in first-seen order.

    Each item is (signal_name, routes), where routes is a list of
    (sender, receiver) tuples. A repeated signal is therefore one enum
    identity with multiple collaboration routes.
    """
    signals = {}
    for sig, sender, receiver in all_signals(model):
        if sig not in signals:
            signals[sig] = []
        route = (sender, receiver)
        if route not in signals[sig]:
            signals[sig].append(route)

    for sig, routes in signals.items():
        yield sig, routes


def generate_signals_hpp(
    model: Model,
    source_name: str,
    enum_name: str,
    max_signal: str,
) -> str:
    signals = list(unique_signals(model))
    out = [
        "#pragma once",
        "",
        f"// GENERATED from {source_name}; do not edit by hand.",
        '// Regenerate with collabc.py.',
        "",
        '#include "qpcpp.hpp"',
        "",
        f"enum {enum_name} {{",
    ]

    for i, (sig, routes) in enumerate(signals):
        init = " = QP::Q_USER_SIG" if i == 0 else ""

        if len(routes) == 1:
            sender, receiver = routes[0]
            out.append(
                f"    {sig}_SIG{init},"
                f"  // {sender} -> {receiver}"
            )
        else:
            out.append("    // routes:")
            for sender, receiver in routes:
                out.append(f"    //   {sender} -> {receiver}")
            out.append(f"    {sig}_SIG{init},")

    out.append("")
    out.append(f"    {max_signal}")
    out.append("};")
    out.append("")
    return "\n".join(out)



def inspect_qm(model: Model, qm_path: Path, aliases: dict[str, str]) -> tuple[int, int]:
    """Conservative cross-model inspection: identity, signal declaration, trigger.

    This does not prove posting, publishing, subscriptions, or runtime delivery.
    Timers are deliberately reported as undetermined in this first pass.
    """
    try:
        root = ET.parse(qm_path).getroot()
    except ET.ParseError as exc:
        raise ModelError(f"{qm_path}: invalid QM XML: {exc}") from exc

    classes = {
        node.get("name"): node
        for node in root.iter("class")
        if node.get("name")
    }
    from qm_signals import declared_signals
    signals = declared_signals(root)

    failures = 0
    unknown = 0
    for signal, sender, receiver in all_signals(model):
        mapped_sender = aliases.get(sender, sender)
        mapped_receiver = aliases.get(receiver, receiver)
        if model.roles.get(sender) == "TIMER":
            print(f"UNDETERMINED: {sender}->{receiver} {signal}: "
                  "timer binding/delivery is not checked in pass 1")
            unknown += 1
            continue
        if model.roles.get(sender) == "EXTERNAL":
            if mapped_receiver not in classes:
                print(f"UNDETERMINED: {sender}->{receiver} {signal}: "
                      f"QM receiver identity unresolved: {mapped_receiver}; "
                      "external sender is not expected to be a QM class")
                unknown += 1
                continue
            qm_signal = signal + "_SIG"
            if qm_signal not in signals:
                print(f"MISSING: {sender}->{receiver} {signal}: "
                      f"{qm_signal} not found in supported QM signal declarations")
                failures += 1
                continue
            receiver_class = classes[mapped_receiver]
            triggers = {
                name.strip().removesuffix("_SIG")
                for transition in receiver_class.iter("tran")
                for name in (transition.get("trig") or "").split(",")
            }
            if signal not in triggers:
                print(f"MISSING: {sender}->{receiver} {signal}: "
                      f"no {signal} trigger in QM class {mapped_receiver}")
                failures += 1
            else:
                print(f"PARTIAL: {sender}->{receiver} {signal}: "
                      f"{qm_signal} declared and {mapped_receiver} handles {signal}; "
                      "external origin and delivery not checked")
            continue
        if mapped_sender not in classes or mapped_receiver not in classes:
            absent = [name for name in (mapped_sender, mapped_receiver)
                      if name not in classes]
            print(f"UNDETERMINED: {sender}->{receiver} {signal}: "
                  f"QM class identity unresolved: {', '.join(absent)}")
            unknown += 1
            continue
        qm_signal = signal + "_SIG"
        if qm_signal not in signals:
            print(f"MISSING: {sender}->{receiver} {signal}: "
                  f"{qm_signal} not found in supported QM signal declarations")
            failures += 1
            continue
        receiver_class = classes[mapped_receiver]
        triggers = set()
        for transition in receiver_class.iter("tran"):
            for name in (transition.get("trig") or "").split(","):
                triggers.add(name.strip().removesuffix("_SIG"))
        if signal not in triggers:
            print(f"MISSING: {sender}->{receiver} {signal}: "
                  f"no {signal} trigger in QM class {mapped_receiver}")
            failures += 1
        else:
            print(f"PARTIAL: {sender}->{receiver} {signal}: "
                  f"{qm_signal} declared and {mapped_receiver} handles {signal}; "
                  "emission/delivery not checked")
    print(f"QM inspection: {failures} missing, {unknown} undetermined; "
          "PARTIAL does not establish an end-to-end match")
    return failures, unknown


def parse_qm_aliases(entries: list[str]) -> dict[str, str]:
    aliases = {}
    for entry in entries:
        if "=" not in entry:
            raise ModelError(f"invalid --qm-map {entry!r}; expected CollabName=QMName")
        source, target = entry.split("=", 1)
        if not AO_RE.fullmatch(source) or not AO_RE.fullmatch(target):
            raise ModelError(f"invalid --qm-map {entry!r}; names must be identifiers")
        if source in aliases:
            raise ModelError(f"duplicate --qm-map for {source}")
        aliases[source] = target
    return aliases


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and compile a .collab AO collaboration model."
    )
    parser.add_argument("input", type=Path, help="input .collab file")
    parser.add_argument(
        "-o", "--out-dir", type=Path,
        help="output directory (default: input file directory)"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="validate only; generate no files"
    )
    parser.add_argument(
        "--puml-only", action="store_true",
        help="generate PlantUML only"
    )
    parser.add_argument(
        "--signals-only", action="store_true",
        help="generate C++ signal header only"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="treat house-convention warnings as errors"
    )
    parser.add_argument(
        "--enum-name", default="AppSignals",
        help="generated C++ enum name (default: AppSignals)"
    )
    parser.add_argument(
        "--max-signal", default="MAX_APP_SIG",
        help="final generated enum member (default: MAX_APP_SIG)"
    )
    parser.add_argument("--qm", type=Path, help="inspect against a QM XML model (read-only)")
    parser.add_argument("--qm-signals", action="store_true",
                        help="inventory QM signal declarations and usage, including incomplete routes")
    parser.add_argument("--qm-reverse", action="store_true",
                        help="inventory QM routes absent from the collaboration contract (advisory)")
    parser.add_argument("--qm-delivery", action="store_true",
                        help="also inspect QM posting, pub/sub and timer source patterns")
    parser.add_argument("--qm-map", action="append", default=[], metavar="COLLAB=QM",
                        help="explicit participant identity mapping; repeat as needed")
    args = parser.parse_args()

    if args.puml_only and args.signals_only:
        parser.error("--puml-only and --signals-only are mutually exclusive")

    try:
        model = parse_model(args.input)
    except (OSError, ModelError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in model.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if args.strict and model.warnings:
        print(
            f"ERROR: {len(model.warnings)} warning(s) under --strict",
            file=sys.stderr,
        )
        return 3

    print(
        f"OK: {len(model.aos)} participant(s), "
        f"{len(model.collaborations)} collaboration(s), "
        f"{sum(1 for _ in unique_signals(model))} signal(s)"
    )

    if args.qm:
        try:
            aliases = parse_qm_aliases(args.qm_map)
            missing, _undetermined = inspect_qm(model, args.qm, aliases)
            if args.qm_delivery:
                from qm_delivery import inspect_delivery
                delivery_missing, _delivery_unknown = inspect_delivery(model, args.qm, aliases)
                missing += delivery_missing
            if args.qm_signals:
                from qm_signals import inspect_signals
                inspect_signals(model, args.qm, aliases)
            if args.qm_reverse:
                from qm_reverse import inspect_reverse
                inspect_reverse(model, args.qm, aliases)
        except (OSError, ModelError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if missing:
            return 4
    elif args.qm_map or args.qm_delivery or args.qm_reverse or args.qm_signals:
        parser.error("--qm-map, --qm-delivery, --qm-reverse and --qm-signals require --qm")

    if args.check:
        return 0

    out_dir = args.out_dir or args.input.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem

    if not args.signals_only:
        puml_path = out_dir / f"{stem}.puml"
        puml_path.write_text(
            generate_puml(model, args.input.name),
            encoding="utf-8",
        )
        print(f"generated: {puml_path}")

    if not args.puml_only:
        hpp_path = out_dir / f"{stem}-signals.hpp"
        hpp_path.write_text(
            generate_signals_hpp(
                model,
                args.input.name,
                args.enum_name,
                args.max_signal,
            ),
            encoding="utf-8",
        )
        print(f"generated: {hpp_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
