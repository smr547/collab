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
    seen_signals = {}

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

            if stripped.startswith("ao "):
                parts = stripped.split()
                if len(parts) != 2:
                    raise ModelError(f"{path}:{idx}: expected 'ao <AOName>'")
                name = parts[1]
                if not AO_RE.match(name):
                    raise ModelError(f"{path}:{idx}: invalid AO name '{name}'")
                if name in seen_aos:
                    raise ModelError(f"{path}:{idx}: duplicate AO '{name}'")
                seen_aos.add(name)
                model.aos.append(name)
                if not name.endswith("AO"):
                    model.warnings.append(
                        f"{path}:{idx}: AO '{name}' does not end in 'AO' "
                        "(house convention)"
                    )
                continue

            if stripped.startswith("collaboration "):
                parts = stripped.split()
                if len(parts) != 3:
                    raise ModelError(
                        f"{path}:{idx}: expected "
                        "'collaboration <AO1> <AO2>'"
                    )
                a, b = parts[1], parts[2]
                if a == b:
                    raise ModelError(
                        f"{path}:{idx}: collaboration endpoints must differ"
                    )
                for name in (a, b):
                    if name not in seen_aos:
                        raise ModelError(
                            f"{path}:{idx}: AO '{name}' has not been declared"
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
        if signal in seen_signals:
            prev = seen_signals[signal]
            raise ModelError(
                f"{path}:{idx}: duplicate signal '{signal}' "
                f"(first declared at line {prev})"
            )
        seen_signals[signal] = idx
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
        raise ModelError(f"{path}: no AOs declared")
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
    out = [
        "@startuml",
        f"' GENERATED from {source_name}; do not edit by hand.",
        f"title {model.title}",
        "",
        "skinparam linetype ortho",
        "top to bottom direction",
        "",
    ]

    for ao in model.aos:
        out.append(f'component "{ao}" as {ao}')

    out.append("")

    for collab in model.collaborations:
        arrow = puml_arrow(collab)
        out.append(f"{collab.a} {arrow} {collab.b}")
        out.append("note on link")
        for n, flow in enumerate(collab.flows):
            if n:
                out.append("")
            out.append(f"  {flow.sender} -> {flow.receiver}")
            for sig in flow.signals:
                out.append(f"    {sig}")
        out.append("end note")
        out.append("")

    out.append("@enduml")
    out.append("")
    return "\n".join(out)


def all_signals(model: Model):
    for collab in model.collaborations:
        for flow in collab.flows:
            for sig in flow.signals:
                yield sig, flow.sender, flow.receiver


def generate_signals_hpp(
    model: Model,
    source_name: str,
    enum_name: str,
    max_signal: str,
) -> str:
    signals = list(all_signals(model))
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

    for i, (sig, sender, receiver) in enumerate(signals):
        init = " = QP::Q_USER_SIG" if i == 0 else ""
        out.append(
            f"    {sig}_SIG{init},"
            f"  // {sender} -> {receiver}"
        )

    out.append("")
    out.append(f"    {max_signal}")
    out.append("};")
    out.append("")
    return "\n".join(out)


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
        f"OK: {len(model.aos)} AO(s), "
        f"{len(model.collaborations)} collaboration(s), "
        f"{sum(1 for _ in all_signals(model))} signal(s)"
    )

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
