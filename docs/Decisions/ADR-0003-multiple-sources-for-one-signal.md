# ADR-0003: Allow One Signal to Have Multiple Sources When Receiver Semantics Are Identical

- **Status:** Proposed
- **Date:** 2026-08-17
- **Project:** collab
- **Related:** ADR-0001 — Establish `collab` as a Textual Collaboration Modelling Language
- **Related:** ADR-0002 — Model AO-Local Signals Separately from Inter-AO Collaboration Signals

## Context

The first Rain Gauge collaboration model exposed a case in which the same semantic signal legitimately originates from two different sources and is delivered to the same receiving Active Object.

The relevant signal is:

```text
BUCKET_SWITCH_CLOSING
```

It can originate from:

```text
BucketReedSwitchISR -> BucketSensorAO
    BUCKET_SWITCH_CLOSING
```

and also from:

```text
ControlAO -> BucketSensorAO
    BUCKET_SWITCH_CLOSING
```

The two sources represent different provenance:

- `BucketReedSwitchISR` reports that the reed-switch hardware has begun closing while the processor is already awake.
- `ControlAO` may report the same fact after waking and interpreting the processor wake reason.

However, from the perspective of `BucketSensorAO`, the meaning is identical:

> **The rain-bucket reed switch has begun closing; begin processing this as the start of a possible bucket tip.**

`BucketSensorAO` does not need to know which source supplied that information in order to determine its behaviour.

The current `collabc` compiler rejects the second occurrence because it enforces global uniqueness of signal declarations:

```text
ERROR: rain-gauge.collab:35: duplicate signal 'BUCKET_SWITCH_CLOSING'
(first declared at line 16)
```

This reveals that the version-1 rule:

> one signal name may appear only once in a `.collab` model

is too restrictive.

The modelling issue is deeper than duplicate syntax. It concerns the relationship between:

- signal identity;
- event meaning;
- event provenance; and
- receiver behaviour.

## Decision

A signal name may appear in more than one directional collaboration declaration when those occurrences represent the **same semantic stimulus**.

The compiler shall treat repeated occurrences of the same signal name as references to one application signal, not as requests to generate duplicate C++ enum members.

For the Rain Gauge:

```text
BucketReedSwitchISR -> BucketSensorAO
    BUCKET_SWITCH_CLOSING

ControlAO -> BucketSensorAO
    BUCKET_SWITCH_CLOSING
```

shall be legal and shall generate only one C++ signal:

```cpp
BUCKET_SWITCH_CLOSING_SIG
```

The governing semantic principle is:

> **Signal identity represents meaning at the receiver, not necessarily provenance at the sender.**

A signal may therefore have multiple sources when the receiver interprets the signal identically and does not require source identity in order to determine its behaviour.

## Receiver-Centric Rule

Signal reuse is appropriate when all of the following are true:

1. the repeated signal denotes the same semantic fact or stimulus;
2. the receiving AO interprets all occurrences identically;
3. the receiving AO does not need sender identity to select different behaviour; and
4. no payload difference is required merely to reconstruct provenance.

The Rain Gauge case satisfies these conditions.

For both sources:

```text
BUCKET_SWITCH_CLOSING
```

means the same thing to `BucketSensorAO`, and the same HSM transition logic should apply.

## When Signals Should Remain Distinct

Signals should remain distinct when source identity materially changes the receiver's behaviour or state.

For example:

```text
BUCKET_SENSOR_IDLE
RADIO_IDLE
```

should remain separate signals to `ControlAO` because `ControlAO` is tracking distributed quiescence and must know which collaborator became idle.

A generic signal:

```text
SENSOR_IDLE
```

would be insufficient unless the event carried an explicit source identifier or equivalent payload.

The preferred modelling form should preserve HSM clarity.

Where distinct signals allow the receiving HSM to express behaviour literally:

```text
BUCKET_SENSOR_IDLE
    / mark bucket sensor idle

RADIO_IDLE
    / mark radio idle
```

they may be preferable to a generic signal followed by procedural branching on an event payload.

## Provenance Is Not Signal Identity

`collab` shall distinguish between the semantic identity of a signal and the routes by which it can arrive.

Conceptually:

```text
Signal:
    BUCKET_SWITCH_CLOSING

Routes:
    BucketReedSwitchISR -> BucketSensorAO
    ControlAO           -> BucketSensorAO
```

The application signal catalogue contains one signal identity.

The collaboration model contains multiple routes carrying that signal.

This means that the compiler's internal model should no longer treat each signal occurrence as a globally unique declaration.

Instead it should maintain:

```text
signal identity
    |
    +-- one or more collaboration routes
    +-- optional AO-local ownership/use
```

subject to semantic validation.

## Generated C++ Signal Catalogue

Repeated collaboration occurrences of one signal generate one enum member.

For example:

```cpp
enum AppSignals {
    BUCKET_SWITCH_CLOSING_SIG = QP::Q_USER_SIG,
    BUCKET_TIPPED_SIG,
    BUCKET_SENSOR_BUSY_SIG,
    BUCKET_SENSOR_IDLE_SIG,
    RAIN_BUCKET_FAULT_SIG,
    SEND_REPORT_SIG,
    RADIO_BUSY_SIG,
    RADIO_IDLE_SIG,

    MAX_APP_SIG
};
```

The generated header should, where practical, preserve all known routes as comments.

For example:

```cpp
BUCKET_SWITCH_CLOSING_SIG = QP::Q_USER_SIG,
    // BucketReedSwitchISR -> BucketSensorAO
    // ControlAO           -> BucketSensorAO
```

The exact formatting is an implementation concern.

## PlantUML Generation

Each collaboration continues to show the signals that travel across that relationship.

Therefore the same signal may appear in more than one collaboration note.

For example, `BUCKET_SWITCH_CLOSING` may be rendered in both:

```text
BucketReedSwitchISR -> BucketSensorAO
```

and:

```text
ControlAO -> BucketSensorAO
```

This is not duplication in the semantic model. It is one signal travelling over two valid collaboration routes.

## Validation

The compiler shall no longer reject a repeated signal name merely because it has appeared previously.

Instead, repeated signals must be validated against their semantic use.

For the initial implementation, the following rule is adopted:

> **A repeated inter-AO signal name is permitted when every occurrence has the same receiver.**

This rule is intentionally conservative.

It directly supports the Rain Gauge case while preventing accidental reuse of the same name for unrelated meanings delivered to different receivers.

Example permitted:

```text
A -> C
    DATA_READY

B -> C
    DATA_READY
```

Example rejected initially:

```text
A -> B
    DATA_READY

C -> D
    DATA_READY
```

because identical spelling across unrelated receiver contexts may represent accidental semantic collision.

A future ADR may relax this constraint if a real application demonstrates a valid case in which one semantic signal should intentionally be delivered to multiple receivers.

## Interaction with AO-Local Signals

ADR-0002 introduced AO-local/internal signals.

An AO-local signal and an inter-AO signal should not automatically be treated as different merely because their routes differ.

If a future design intentionally uses one semantic signal both:

- as an externally received event; and
- as a self-posted event within the same AO,

that case should be evaluated according to the same receiver-centric principle.

The implementation should therefore evolve toward a signal table based on semantic identity plus routes/uses, rather than separate unrelated registries.

This ADR does not require full support for every mixed internal/external case immediately, but the compiler design should avoid making such support impossible.

## Per-Signal Documentation

Because one signal can have several routes, documentation increasingly belongs to the signal identity as well as to each occurrence.

For example:

```text
BUCKET_SWITCH_CLOSING
```

has one semantic description:

> The bucket reed switch has begun closing.

while each route may have different provenance or operational context.

The language currently permits inline `#` comments on signal occurrences. These comments remain useful.

A future language extension may distinguish:

- a signal's canonical semantic description; and
- route-specific comments.

No new syntax is required by this ADR.

## Rationale

### Model semantic facts rather than transport history

The receiving HSM should react to what happened, not necessarily to how knowledge of it arrived.

In the Rain Gauge case, both the ISR and `ControlAO` communicate the same fact. Encoding the source into two different signal names would create artificial behavioural distinctions.

### Preserve literal HSM behaviour

A single:

```text
BUCKET_SWITCH_CLOSING
```

transition in `BucketSensorAO` accurately represents the physical meaning.

Creating:

```text
ISR_BUCKET_SWITCH_CLOSING
CONTROL_BUCKET_SWITCH_CLOSING
```

would force duplicated transitions or unnecessary convergence even though the HSM behaviour is identical.

### Keep provenance available in the collaboration model

Allowing signal reuse does not erase source information.

The `.collab` routes still show every sender and receiver, while the generated enum represents the semantic event identity.

### Avoid unnecessary payloads

Sender identity should not be added to event payloads when the receiver does not need it.

If provenance becomes behaviorally relevant, then either distinct signals or an explicit event parameter can be considered.

## Consequences

### Positive

- legitimate multi-source signals can be modelled naturally;
- the generated enum reflects semantic signal identity rather than route count;
- receiving HSMs remain concise and literal;
- collaboration diagrams still preserve provenance;
- artificial sender-specific signal names are avoided where sender identity is irrelevant;
- the compiler model becomes closer to the semantics of event-driven systems.

### Costs and risks

- signal handling in the compiler becomes more sophisticated;
- generated comments may need to represent multiple routes;
- accidental reuse becomes possible unless validation remains strong;
- receiver-based validation is a conservative heuristic rather than a complete semantic proof;
- future cases may require explicit language support for shared signals across multiple receivers.

## Alternatives Considered

### Require globally unique signal declarations

This is the current implementation.

Rejected because it prevents a valid case in which one semantic event reaches the same receiver from multiple sources.

### Encode sender identity in every signal name

For example:

```text
ISR_BUCKET_SWITCH_CLOSING
CONTROL_BUCKET_SWITCH_CLOSING
```

Rejected because the receiver does not care about the distinction and the HSM behaviour would become less literal.

### Use one generic signal plus sender payload

Rejected for this case because the sender is not needed by the receiver.

Adding unused provenance to the event data would increase coupling without changing behaviour.

## Compiler Changes

The compiler should replace the current global:

```text
signal name -> first declaration line
```

uniqueness check with a semantic signal registry.

Conceptually:

```text
signal name
    semantic identity
    receivers
    routes:
        sender -> receiver
        sender -> receiver
```

For the initial implementation:

1. first occurrence creates the signal identity;
2. later occurrence with the same receiver adds another route;
3. later occurrence with a different receiver produces an error;
4. code generation emits one enum member per signal identity;
5. PlantUML generation continues to emit each signal on every declared route.

Tests should cover at least:

- one signal on one route;
- one signal from two senders to the same receiver;
- one signal repeated within the same directional group;
- one signal reused for different receivers;
- deterministic enum order;
- preservation of all routes in generated comments.

## Emerging Design Principle

This ADR establishes a candidate design practice that extends beyond the `collab` compiler:

> **Name an event for the semantic stimulus perceived by the receiver. Encode provenance only when provenance matters to behaviour.**

This principle should be tested against further embedded HSM designs before being treated as a universal rule.

## Summary

`collab` will allow one signal to travel over multiple collaboration routes when those routes deliver the same semantic stimulus to the same receiving AO.

The Rain Gauge example:

```text
BucketReedSwitchISR -> BucketSensorAO
    BUCKET_SWITCH_CLOSING

ControlAO -> BucketSensorAO
    BUCKET_SWITCH_CLOSING
```

represents one application signal with two sources.

The generated C++ enum shall contain one `BUCKET_SWITCH_CLOSING_SIG`, while the collaboration model and generated diagram retain both routes.

This changes the meaning of signal uniqueness from:

> **one declaration per name**

to:

> **one semantic signal identity, potentially carried over multiple routes.**
