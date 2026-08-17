# How to Write `.collab` Files

## Purpose

A `.collab` file is the **authoritative textual model of collaboration between Active Objects**.

It describes:

- which Active Objects exist;
- which pairs of Active Objects collaborate;
- which signals travel across each collaboration; and
- the direction in which each signal travels.

The `.collab` model deliberately does **not** describe the internal HSM behaviour of an Active Object. QM remains authoritative for that.

The toolchain is:

```text
.collab
   |
   +--> validation of collaboration house rules
   |
   +--> generated PlantUML (.puml)
   |
   +--> generated QP C++ signal enum (*-signals.hpp)
```

The `.collab` file is therefore the source of truth. The `.puml` and `.hpp` files are generated artefacts.

---

## 1. Minimal Example

```text
collab 1
title "Rain Gauge — AO Collaboration"

ao BucketSensorAO
ao ControlAO

collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
end
```

This says:

- the model uses `.collab` language version 1;
- two AOs exist;
- they collaborate;
- all four signals travel from `BucketSensorAO` to `ControlAO`;
- there are no signals in the opposite direction.

The compiler derives the arrowhead on the collaboration line from the signal directions.

---

## 2. File Header

Every file should begin with:

```text
collab 1
```

Version 1 is the initial language defined by ADR-0002 and the Rain Gauge work.

A title is strongly recommended:

```text
title "Rain Gauge — AO Collaboration"
```

Quoted titles may contain spaces and punctuation.

---

## 3. Declaring Active Objects

Declare each Active Object once:

```text
ao BucketSensorAO
ao ControlAO
ao RadioAO
```

### House convention

AO names should end in `AO`.

For example:

```text
BucketSensorAO
ControlAO
RadioAO
```

The compiler accepts a legal identifier that does not end in `AO`, but reports a warning.

AO names use normal C/C++ identifier syntax:

```text
[A-Za-z_][A-Za-z0-9_]*
```

---

## 4. Declaring a Collaboration

A collaboration is a relationship between exactly two AOs:

```text
collaboration BucketSensorAO ControlAO
```

It ends with:

```text
end
```

A pair of AOs may have only one collaboration declaration.

This embodies the collaboration-diagram house style:

> **One solid collaboration line joins a pair of collaborating AOs. Signals are grouped by direction on that collaboration.**

---

## 5. Declaring Signal Direction

Inside a collaboration, declare a directional signal group:

```text
BucketSensorAO -> ControlAO
```

Then indent the signals belonging to that direction:

```text
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
```

Signals use `UPPER_SNAKE_CASE`.

The compiler appends `_SIG` when generating the C++ enum:

```text
BUCKET_TIPPED
```

becomes:

```cpp
BUCKET_TIPPED_SIG
```

---

## 6. Bidirectional Collaboration

If signals travel in both directions, declare two grouped flows within the same collaboration:

```text
collaboration ControlAO RadioAO
  ControlAO -> RadioAO
    TRANSMIT_REPORT

  RadioAO -> ControlAO
    RADIO_BUSY
    RADIO_IDLE
    RADIO_FAULT
    TRANSMIT_COMPLETE
end
```

The generated collaboration line will have arrowheads at both ends.

There is still only **one collaboration** between `ControlAO` and `RadioAO`.

---

## 7. Unidirectional Collaboration

If signals travel in only one direction, declare only that direction:

```text
collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
end
```

The generated line will have one arrowhead.

Do not add an empty reverse direction merely for symmetry.

---

## 8. Comments

A `#` begins a comment:

```text
# BucketSensorAO reports semantic results, not raw GPIO edges.
collaboration BucketSensorAO ControlAO
```

End-of-line comments are also permitted:

```text
ao ControlAO   # system-level coordinator
```

---

## 9. Signal Naming House Convention

Signal names must be globally unique within a `.collab` model.

Signals should preserve enough domain or sender identity to remain unambiguous as the system grows.

Prefer:

```text
BUCKET_SENSOR_BUSY
BUCKET_SENSOR_IDLE
RAIN_BUCKET_FAULT
RADIO_BUSY
RADIO_IDLE
```

over generic names such as:

```text
SENSOR_BUSY
SENSOR_IDLE
SENSOR_FAULT
```

The current compiler warns about the three generic names above.

The compiler does not attempt to infer every possible naming mistake. Human review remains important.

---

## 10. What the Compiler Validates

Version 1 validates:

- supported `.collab` language version;
- legal AO names;
- duplicate AO declarations;
- references to undeclared AOs;
- duplicate collaborations between the same pair;
- collaboration endpoints must differ;
- directional flow endpoints must match the containing collaboration;
- duplicate directional groups;
- every collaboration must contain at least one signal flow;
- every flow must contain at least one signal;
- signal names must use `UPPER_SNAKE_CASE`;
- signal names must be globally unique;
- selected departures from house naming conventions.

Errors stop generation.

Warnings do not stop generation unless `--strict` is used.

---

## 11. Generated PlantUML

For:

```text
collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
end
```

the generated PlantUML contains one collaboration link:

```plantuml
BucketSensorAO --> ControlAO
```

and an attached note containing the grouped directional signals.

The generated PlantUML also requests:

```plantuml
skinparam linetype ortho
```

to express the preference for straight lines and 90-degree bends rather than curved lines.

Do not edit the generated `.puml` as the authoritative design. Change the `.collab` file and regenerate.

---

## 12. Generated C++ Signal Enum

The same source produces a QP-compatible header similar to:

```cpp
#pragma once

#include "qpcpp.hpp"

enum AppSignals {
    BUCKET_TIPPED_SIG = QP::Q_USER_SIG,
    BUCKET_SENSOR_BUSY_SIG,
    BUCKET_SENSOR_IDLE_SIG,
    RAIN_BUCKET_FAULT_SIG,

    MAX_APP_SIG
};
```

The generated header also records the sender and receiver beside each signal as a comment.

The precise enum naming can be selected on the compiler command line.

---

## 13. Compiler Commands

Make the compiler executable:

```bash
chmod +x collabc.py
```

Validate only:

```bash
./collabc.py rain-gauge.collab --check
```

Validate with house-convention warnings treated as errors:

```bash
./collabc.py rain-gauge.collab --check --strict
```

Generate both PlantUML and the signal header:

```bash
./collabc.py rain-gauge.collab
```

This creates:

```text
rain-gauge.puml
rain-gauge-signals.hpp
```

Generate into another directory:

```bash
./collabc.py rain-gauge.collab -o generated
```

Generate only PlantUML:

```bash
./collabc.py rain-gauge.collab --puml-only
```

Generate only the signal header:

```bash
./collabc.py rain-gauge.collab --signals-only
```

Choose the C++ enum and terminal enum-member names:

```bash
./collabc.py rain-gauge.collab \
    --enum-name Signals \
    --max-signal MAX_SIG
```

---

## 14. Rendering the Diagram

After compilation:

```bash
plantuml -tsvg rain-gauge.puml
```

This produces:

```text
rain-gauge.svg
```

PNG can be generated with:

```bash
plantuml rain-gauge.puml
```

The `.collab` remains authoritative; the `.puml`, `.svg`, `.png`, and generated C++ are derived views or implementation artefacts.

---

## 15. Recommended Repository Layout

A useful initial layout is:

```text
qp-lab/
    rain-gauge/
        model/
            rain-gauge.collab
            rain-gauge.puml
            rain-gauge-signals.hpp

        tools/
            collabc.py

        docs/
            collab-language.md
```

As the Rain Gauge becomes a broader weather station, the language and compiler can evolve without changing the principle that the collaboration model owns the inter-AO signal vocabulary.

---

## 16. Deliberate Limits of Version 1

Version 1 does **not** yet model:

- event payload types;
- publish/subscribe versus direct posting;
- signal priorities;
- multiplicities;
- AO deployment to processors or cores;
- HSM states;
- timer declarations;
- synchronous calls;
- inheritance;
- generated QP event classes.

These are deliberate omissions.

The language should grow only when a concrete design need appears.

The guiding rule is:

> **Keep the collaboration model semantic, readable, and smaller than the implementation it generates.**

---

## 17. Relationship to QM

`.collab` and QM have complementary authority.

```text
.collab
    authoritative for:
        AOs participating in the system
        collaborations between AOs
        inter-AO signal vocabulary
        signal direction

QM
    authoritative for:
        internal HSM states
        transitions
        entry/exit actions
        state-local behaviour
        executable HSM code generation
```

The generated C++ signal catalogue is the bridge between these modelling levels.

A useful working principle is:

> **State machines describe behaviour within an object. Signals describe contracts between objects.**
