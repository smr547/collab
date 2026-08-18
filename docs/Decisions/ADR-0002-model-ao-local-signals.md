# ADR-0002: Model AO-Local Signals Separately from Inter-AO Collaboration Signals

- **Status:** Proposed
- **Date:** 2026-08-17
- **Project:** collab
- **Related:** ADR-0001 — Establish `collab` as a Textual Collaboration Modelling Language

## Context

ADR-0001 established `.collab` as the authoritative textual model for Active Object collaboration and the inter-AO signal vocabulary, with generated PlantUML and C++ signal declarations.

The first real modelling exercise, the Rain Gauge collaboration, exposed an important limitation in that initial assumption.

Not every signal used by an Active Object crosses an AO boundary.

In particular, an HSM may post an event to itself. The proposed `BucketSensorAO` design is expected to use self-posted observation/reminder events in order to preserve explicit HSM behaviour while keeping run-to-completion actions short and non-blocking.

Conceptually:

```text
TIMEOUT action
    read GPIO
    post SWITCH_OPEN or SWITCH_CLOSED to self
```

The resulting signals:

```text
SWITCH_OPEN
SWITCH_CLOSED
```

are genuine members of the application's QP signal vocabulary. They must therefore appear in the generated C++ signal enum.

However, they are not part of an inter-object collaboration.

Representing them as a fake collaboration such as:

```text
collaboration BucketSensorAO BucketSensorAO
```

would weaken the meaning of `collaboration`, which is intended to describe communication between distinct participants.

The first Rain Gauge exercise therefore demonstrates that the application signal vocabulary has at least two semantic categories:

```text
Application signal vocabulary
    |
    +-- inter-AO collaboration signals
    |
    +-- AO-local/internal signals
```

Both categories need to contribute to the generated C++ enum, but only the first belongs in the collaboration diagram.

The same modelling exercise also clarified two related house conventions:

1. directional declarations should use canonical sender-first notation:

```text
A -> B
```

and reverse traffic should be written:

```text
B -> A
```

rather than:

```text
A <- B
```

2. per-signal comments are useful and should be preserved where practical because they improve readability and can document signal intent.

## Decision

Extend the `.collab` language with an explicit construct for AO-local/internal signals.

The canonical form will be:

```text
internal-signals BucketSensorAO
    SWITCH_OPEN
    SWITCH_CLOSED
    CONFIRM_TIMEOUT
end
```

This construct means:

> These signals belong to the executable application signal vocabulary and are used internally by the named AO, but they are not part of an inter-AO collaboration.

The exact signal set shown above is illustrative only; individual applications define their own internal signal names.

The compiler will merge:

```text
inter-AO collaboration signals
+
AO-local/internal signals
=
generated application signal enum
```

The generated PlantUML collaboration diagram will include only inter-AO collaborations and their directional signal groups.

AO-local signals will not create collaboration lines or self-links in the PlantUML diagram.

## Canonical Direction Syntax

Directional collaboration groups will use sender-first notation only:

```text
SenderAO -> ReceiverAO
```

The reverse direction is written by reversing the participants:

```text
ReceiverAO -> SenderAO
```

The alternative visual form:

```text
SenderAO <- ReceiverAO
```

will not be the preferred house syntax.

The compiler may reject it or accept it with a style warning in a future version, but generated and documented `.collab` examples will use sender-first notation.

The reason is consistency:

> **Every directional declaration reads as sender, arrow, receiver.**

This simplifies parsing, code review, generated documentation, and human interpretation.

## Per-Signal Comments

The existing `#` comment syntax will remain available for documenting individual signals:

```text
BucketSensorAO -> ControlAO
    BUCKET_TIPPED         # valid mechanical bucket tip recognised
    BUCKET_SENSOR_BUSY    # BucketSensorAO is not currently sleep-safe
    BUCKET_SENSOR_IDLE    # BucketSensorAO has returned to sleep-safe state
    RAIN_BUCKET_FAULT     # reed-switch behaviour judged implausible
```

and:

```text
internal-signals BucketSensorAO
    SWITCH_OPEN           # instantaneous reed-switch observation
    SWITCH_CLOSED         # instantaneous reed-switch observation
```

Initially, these comments remain documentation in the authoritative `.collab` source.

The compiler should preserve them where practical in generated textual artefacts such as the C++ signal header.

Whether they should also appear in generated PlantUML is a rendering decision and is not required by this ADR.

## Generated C++ Signal Catalogue

The generated C++ signal catalogue remains a single application-level enum.

For example:

```cpp
enum AppSignals {
    BUCKET_SWITCH_CLOSING_SIG = QP::Q_USER_SIG, // BucketReedSwitchISR -> BucketSensorAO
    BUCKET_TIPPED_SIG,                          // BucketSensorAO -> ControlAO
    BUCKET_SENSOR_BUSY_SIG,                     // BucketSensorAO -> ControlAO
    BUCKET_SENSOR_IDLE_SIG,                     // BucketSensorAO -> ControlAO
    RAIN_BUCKET_FAULT_SIG,                      // BucketSensorAO -> ControlAO

    SWITCH_OPEN_SIG,                            // internal to BucketSensorAO
    SWITCH_CLOSED_SIG,                          // internal to BucketSensorAO
    CONFIRM_TIMEOUT_SIG,                        // internal to BucketSensorAO

    MAX_APP_SIG
};
```

The precise ordering policy remains an implementation concern, but it must be deterministic and stable.

The compiler should clearly identify the provenance of each signal in generated comments where practical:

```text
AO1 -> AO2
internal to AO
```

## PlantUML Generation

Only inter-AO collaborations participate in diagram generation.

For example:

```text
collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
end
```

contributes to the PlantUML collaboration diagram.

By contrast:

```text
internal-signals BucketSensorAO
    SWITCH_OPEN
    SWITCH_CLOSED
    CONFIRM_TIMEOUT
end
```

does not create a visual collaboration.

This preserves the meaning of the collaboration diagram:

> **It describes contracts between collaborating participants, not all events used internally by their HSMs.**

## Validation Rules

The compiler will extend validation to cover AO-local signals.

At minimum:

- the AO named by `internal-signals` must already be declared;
- an `internal-signals` block must contain at least one signal;
- signal names must obey the existing signal naming convention;
- all signal names remain globally unique across both collaboration and internal declarations;
- the same AO may have only one `internal-signals` block, unless future language evolution explicitly changes that rule;
- an internal signal must not also be declared as an inter-AO collaboration signal.

Selected per-signal comments may be preserved but do not affect semantic validation.

## Rationale

### Preserve the meaning of collaboration

A collaboration is a relationship between distinct participants.

Self-posted signals are important to the executable model, but representing them as self-collaborations would blur the distinction between:

```text
communication between objects
```

and:

```text
stimuli used within one object's own behaviour
```

### Preserve one authoritative signal vocabulary

The generated C++ enum still needs all application signals.

By allowing both collaboration signals and AO-local signals in the same `.collab` model, the language remains the single authoritative source of the executable signal catalogue.

### Support explicit HSM design patterns

AO-local signals are particularly important for patterns such as self-posted Reminder-style events, where an HSM performs a short observation or partial computation and posts a made-up event to itself to continue processing in a later RTC step.

The collaboration model should be capable of defining those signals without pretending they cross an AO boundary.

### Maintain separation of modelling concerns

The division becomes:

```text
.collab
    inter-AO collaboration contracts
    AO-local signal declarations
    complete application signal vocabulary

QM
    internal HSM behaviour
    states
    transitions
    actions
    use of those signals
```

This preserves the principle established in ADR-0001 while refining the source of the generated enum.

## Consequences

### Positive

- the generated signal enum can remain complete;
- self-posted signals are modelled explicitly;
- collaboration diagrams remain semantically clean;
- no fake self-collaborations are needed;
- the DSL better matches real QP/QM applications;
- signal provenance becomes clearer;
- Reminder-style HSM designs can be represented without distorting the system collaboration model.

### Costs and risks

- the DSL gains a second signal-declaration construct;
- the compiler must merge two signal sources into one deterministic enum;
- generated artefacts need to preserve clear provenance;
- the distinction between internal and collaboration signals must remain understandable as the language grows;
- further signal categories may eventually emerge, requiring additional modelling decisions.

## Alternatives Considered

### Represent self-signals as self-collaborations

Rejected.

A declaration such as:

```text
collaboration BucketSensorAO BucketSensorAO
```

would make the meaning of `collaboration` inconsistent and would create misleading self-links in generated diagrams.

### Keep internal signals manually in QM/C++

Rejected as the preferred approach.

This would reintroduce multiple authoritative signal catalogues and defeat the goal of generating a complete application signal enum from the system model.

### Treat all signals as globally declared with no owner or provenance

Rejected.

Although simple, this loses useful semantic information about whether a signal crosses an AO boundary or is internal to one AO.

## Language Example

A fuller Rain Gauge fragment may therefore look like:

```text
collab 1
title "Rain Gauge — AO Collaboration"

ao BucketReedSwitchISR
ao BucketSensorAO
ao ControlAO
ao RadioAO

collaboration BucketReedSwitchISR BucketSensorAO
  BucketReedSwitchISR -> BucketSensorAO
    BUCKET_SWITCH_CLOSING
end

collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
    RAIN_BUCKET_FAULT
end

collaboration ControlAO RadioAO
  ControlAO -> RadioAO
    SEND_REPORT

  RadioAO -> ControlAO
    RADIO_BUSY
    RADIO_IDLE
end

internal-signals BucketSensorAO
    SWITCH_OPEN
    SWITCH_CLOSED
    CONFIRM_TIMEOUT
end
```

This model contains both the system collaboration contracts and the AO-local event vocabulary required for code generation.

## Emerging Design Principle

This ADR refines the broader modelling principle:

> **Inter-object signals describe collaboration contracts; AO-local signals describe internal stimuli. Both belong to the executable event vocabulary, but only the former belong in the collaboration diagram.**

This distinction should be revisited after additional applications exercise the language.

## Next Step

Update the `.collab` language guide and compiler to support:

```text
internal-signals <AOName>
    SIGNAL_NAME
    ...
end
```

while preserving existing version-1 collaboration syntax.

Before implementation, add tests covering:

- valid internal signal declarations;
- undeclared AO ownership;
- duplicate internal blocks;
- duplicate signals across internal and collaboration declarations;
- empty internal blocks;
- per-signal comments; and
- deterministic generated enum output.

This ADR records the decision to extend `collab` so the `.collab` model remains authoritative for the complete application signal vocabulary without weakening the semantics of collaboration.
