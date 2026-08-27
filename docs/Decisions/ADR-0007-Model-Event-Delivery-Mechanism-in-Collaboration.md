# ADR-0007: Model Event Delivery Mechanism in Collaborations

* **Status:** Accepted
* **Date:** 2026-08-19
* **Project:** collab / HSM model tooling
* **Related:** ADR-0003 --- Signal Reuse Across Multiple Routes
* **Related:** ADR-0004 --- Model Completeness and Unified Signal
  Generation
* **Related:** ADR-0006 --- Peer System Models and Model-Driven
  Toolchain

## Context

QP provides two important event-delivery mechanisms between Active
Objects:

1. **Direct Posting (D/P)** --- an event is posted directly to a
   particular recipient Active Object.
2. **Publish/Subscribe (P/S)** --- an event is published by signal and
   delivered by QP to Active Objects that have subscribed to that
   signal.

The original `collab` language and collaboration diagram naturally
represent direct posting.

A collaboration is established between a pair of participants. For that
collaboration there are two directional sets of signals:

```text
A -> B
B -> A
```

Each set can contain zero, one, or many signals, but at least one of the
two sets must be non-empty. If both were empty there would be no
communication and therefore no collaboration to represent.

Publish/subscribe initially appears different because the publisher does
not name its recipients. Nevertheless, once a consumer subscribes to a
published signal, an effective communication route exists:

```text
Publisher -> Subscriber : SIGNAL
```

The delivery mechanism differs, but the semantic fact represented by the
collaboration diagram remains: a signal can travel from one participant
to another.

Therefore P/S need not introduce a separate graphical abstraction such
as an event bus. It can be represented as another delivery mechanism on
the existing signal route.

## Decision

The `collab` model shall represent both direct-post and
publish/subscribe communication using the existing pairwise
collaboration abstraction.

Each signal route has a **delivery mechanism**:

```text
DIRECT
PUBLISH_SUBSCRIBE
```

Direct posting is the default and requires no annotation.

Publish/subscribe is explicitly marked in `.collab` by:

```text
[P/S]
```

For example:

```text
collaboration ControlAO DisplayAO
  ControlAO -> DisplayAO
    WEATHER_UPDATED [P/S]
end
```

This declares the effective route from `ControlAO` to `DisplayAO`, with
publish/subscribe as its delivery mechanism.

An unannotated signal retains the existing direct-post meaning:

```text
collaboration BucketSensorAO ControlAO
  BucketSensorAO -> ControlAO
    BUCKET_TIPPED
end
```

Existing `.collab` models therefore remain valid and retain their
current semantics.

## Collaboration Semantics

A collaboration remains a relationship between a pair of system
participants:

```text
Collaboration(A, B)

    A -> B signals = {0..n}
    B -> A signals = {0..n}
```

with the constraint:

```text
|A -> B| + |B -> A| >= 1
```

Each signal-route member additionally has:

```text
delivery = DIRECT | PUBLISH_SUBSCRIBE
```

P/S therefore extends the signal route rather than changing the
fundamental collaboration abstraction.

## Graphical Representation

The collaboration diagram shall continue to use the same graphical
structure for D/P and P/S communication.

The delivery mechanism shall be shown adjacent to signals whose
mechanism differs from the default:

```text
ControlAO ---------------- DisplayAO

ControlAO -> DisplayAO
    WEATHER_UPDATED [P/S]
    SYSTEM_FAULT    [P/S]
```

Direct-post signals require no annotation:

```text
BucketSensorAO ------------ ControlAO

BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_BUSY
    BUCKET_SENSOR_IDLE
```

No synthetic event-bus, QP, or publish/subscribe broker participant
shall be introduced merely to depict framework machinery. QP implements
delivery but is not thereby a domain collaborator.

The objective is to preserve the existing simplicity of the
collaboration diagram while making delivery semantics visible where they
matter.

## Multiple Subscribers

A published signal can have multiple subscribers:

```text
collaboration ControlAO DisplayAO
  ControlAO -> DisplayAO
    WEATHER_UPDATED [P/S]
end

collaboration ControlAO LoggerAO
  ControlAO -> LoggerAO
    WEATHER_UPDATED [P/S]
end

collaboration ControlAO RadioAO
  ControlAO -> RadioAO
    WEATHER_UPDATED [P/S]
end
```

These declarations represent one semantic signal, `WEATHER_UPDATED`,
with one publisher and three subscribers, while the collaboration model
contains three effective routes.

This is consistent with the signal-reuse principle: the number of routes
does not determine the number of signal identities.

## One Collaboration Can Carry Multiple P/S Signals

A subscription concerns a particular signal, but a pair of participants
may communicate using several published signals:

```text
collaboration ControlAO DisplayAO
  ControlAO -> DisplayAO
    WEATHER_UPDATED [P/S]
    SYSTEM_FAULT    [P/S]
    BATTERY_LOW     [P/S]
end
```

This remains one collaboration containing three P/S signal routes.

There is therefore no rule that a P/S collaboration contains exactly one
signal.

## Signal Identity and Delivery Mechanism

A signal has one semantic identity across the application.

The integrated semantic model shall record, at minimum:

```text
Signal
    name
    delivery mechanism
    route(s)
    publisher(s), where applicable
    subscriber(s), where applicable
```

For the initial implementation, a signal shall not be permitted to use
both direct posting and publish/subscribe on different routes.

For example:

```text
A -> B
    SYSTEM_FAULT [P/S]

A -> C
    SYSTEM_FAULT
```

shall be diagnosed as inconsistent.

This is a modelling decision intended to preserve a clear
application-level communication semantic for each signal. If a real
application later demonstrates a legitimate need for mixed delivery, the
restriction can be reconsidered in a subsequent ADR.

## Publisher and Subscriber Semantics

A P/S route:

```text
A -> B
    SIGNAL [P/S]
```

implies the complementary communication facts:

```text
A publishes SIGNAL
B subscribes to SIGNAL
```

When several routes reuse the same P/S signal, the model compiler shall
reconcile them into a signal-centric view while retaining the pairwise
routes required for collaboration rendering.

For example:

```text
A -> B : SIGNAL [P/S]
A -> C : SIGNAL [P/S]
A -> D : SIGNAL [P/S]
```

implies:

```text
SIGNAL
    publisher: A
    subscribers: B, C, D
```

## Generated Signal Enumeration

Publish/subscribe affects generation of the application signal
enumeration.

The generator must distinguish signals that participate in P/S because
the QP publish/subscribe facility requires a maximum publishable signal
boundary.

The generated enum shall therefore contain an explicit:

```text
MAX_PUB_SIG
```

boundary.

Conceptually:

```cpp
enum AppSignals {
    // Publish/subscribe signals
    WEATHER_UPDATED_SIG = QP::Q_USER_SIG,
    SYSTEM_FAULT_SIG,
    BATTERY_LOW_SIG,

    MAX_PUB_SIG,

    // Non-published application signals
    BUCKET_TIPPED_SIG,
    BUCKET_SENSOR_BUSY_SIG,
    BUCKET_SENSOR_IDLE_SIG,
    TIMEOUT_SIG,

    MAX_APP_SIG
};
```

All application signals that can be published shall occur below
`MAX_PUB_SIG`.

Signals that are direct-posted or local-only and are not published may
occur after that boundary.

The exact generated QP initialization code is outside the scope of this
ADR. The no-P/S case shall be implemented in a form appropriate to the
QP API.

## Ordering of Generated Signals

Because P/S signals must lie below `MAX_PUB_SIG`, enum generation can no
longer rely solely on global first-seen ordering.

The generator shall produce a deterministic ordering with at least two
groups:

1. publish/subscribe-capable signals;
2. remaining application signals.

Within each group, ordering shall be stable and deterministic.

This derived implementation constraint does not change semantic signal
identity.

## `.collab` Language Compatibility

The extension is deliberately minimal.

Existing syntax:

```text
A -> B
    SIGNAL
```

continues to mean direct posting.

New syntax:

```text
A -> B
    SIGNAL [P/S]
```

selects publish/subscribe delivery.

The absence of a delivery annotation always means direct posting.

This preserves existing `.collab` files without migration and keeps the
common case visually uncluttered.

## Parser and Semantic-Model Implications

The `.collab` parser shall associate a delivery mechanism with every
signal route.

For an unannotated route:

```text
delivery = DIRECT
```

For `[P/S]`:

```text
delivery = PUBLISH_SUBSCRIBE
```

The semantic model shall reconcile repeated P/S routes into signal-level
publisher/subscriber information while retaining pairwise routes for
collaboration rendering and model checking.

## `collabc` Implications

`collabc` shall preserve the existing collaboration representation and
add `[P/S]` to generated PlantUML for publish/subscribe signals.

Direct-post signals shall remain unannotated.

The graphical representation should therefore make P/S visible without
materially increasing diagram complexity.

## Enum-Generator Implications

The signal integration / enum generator introduced by ADR-0004 and
placed in the architecture by ADR-0006 shall:

* identify all P/S signals;
* ensure each semantic signal is generated once regardless of
  subscriber count;
* place publishable signals below `MAX_PUB_SIG`;
* generate the explicit `MAX_PUB_SIG` boundary;
* retain `MAX_APP_SIG`;
* reject or diagnose inconsistent delivery semantics for a reused
  signal;
* maintain deterministic output ordering.

## Model-Checking Implications

Publish/subscribe creates useful new cross-model consistency checks.

The model checker should eventually be able to verify that:

* every P/S subscriber declared in `system.collab` has corresponding
  subscription behaviour in `system.qm`;
* every P/S signal published by an AO is consistent with the publisher
  declared by `system.collab`;
* signals declared as direct-posted are not unexpectedly used as P/S
  signals;
* reused P/S signal routes resolve to a consistent semantic signal;
* P/S signals lie below the generated `MAX_PUB_SIG` boundary;
* publishers and subscribers are participants in the complete system
  model.

These checks depend on information exposed by the future QM reader and
should be introduced only when they can be performed reliably.

## Relationship to the Peer System Models

ADR-0006 established:

> `system.collab` is authoritative for system structure and
> communication.

> `system.qm` is authoritative for executable application behaviour.

This ADR makes **delivery mechanism** part of the communication
semantics owned by `system.collab`.

Thus:

```text
system.collab
    says:
        ControlAO -> DisplayAO
        WEATHER_UPDATED [P/S]

system.qm
    should eventually demonstrate:
        ControlAO publishes WEATHER_UPDATED
        DisplayAO subscribes to WEATHER_UPDATED
```

The common semantic/model-checking layer can compare these independent
views.

This is an example of the cross-model reasoning anticipated by ADR-0006.

## Relationship to Signal Reuse

Publish/subscribe provides a particularly strong example of why a signal
must be modelled independently of its routes.

A single published signal can legitimately produce many collaboration
routes:

```text
                    +--> DisplayAO
                    |
ControlAO -- SIGNAL +--> LoggerAO
                    |
                    +--> RadioAO
```

The application still contains one `SIGNAL`, one enum member, and one
publish/subscribe semantic identity.

The collaboration model contains multiple routes because multiple
participants receive it.

## Rationale

### Preserve diagram clarity

P/S changes delivery mechanics, not the fundamental fact that one
participant communicates an event to another.

Representing it as a small annotation on the signal retains the
simplicity of the existing collaboration diagram.

### Keep framework machinery out of the domain model

Introducing an artificial event-bus participant would make QP
infrastructure appear to be a domain collaborator and would obscure the
actual application relationships.

### Make delivery semantics explicit where necessary

The distinction matters to implementation, enum generation,
initialization, and model checking. It therefore belongs in the model.

### Preserve backward compatibility

Direct posting remains the default. Existing `.collab` files require no
changes.

### Support multicast without duplicating signal identity

Multiple P/S subscribers naturally become multiple collaboration routes
referencing one semantic signal.

### Enable stronger model checking

Because the collaboration model declares intended P/S relationships,
future tooling can compare them with actual QM subscription and
publication behaviour.

## Consequences

### Positive

* D/P and P/S fit within one collaboration abstraction;
* existing diagrams remain simple;
* existing `.collab` files remain valid;
* P/S is immediately visible where used;
* multicast relationships remain explicit;
* signal reuse semantics extend naturally to P/S;
* the enum generator gains enough information to generate
  `MAX_PUB_SIG`;
* future tooling can check intended subscriptions and publications
  against `system.qm`;
* no artificial framework participant is introduced into the domain
  model.

### Costs and Risks

* signal routes now carry an additional semantic attribute;
* enum ordering must account for the publishable-signal boundary;
* reused signals require delivery-mechanism consistency checking;
* future QM analysis must reliably identify subscription/publication
  behaviour before strong cross-model checks are enabled;
* mixed D/P and P/S use of one signal is initially prohibited even if
  technically possible in QP.

## Alternatives Considered

### Draw a publish/subscribe event bus

Rejected because it introduces QP infrastructure as though it were a
domain participant and makes a simple application relationship harder to
read.

### Introduce a separate P/S collaboration construct

Rejected because P/S does not change the fundamental pairwise
communication relationship visible to the system designer.

### Leave P/S out of the collaboration model

Rejected because delivery mechanism affects generated signal layout,
framework configuration, model checking, and understanding of system
communication.

### Require explicit `[D/P]` and `[P/S]` on every signal

Rejected because D/P is the established default and mandatory annotation
would add noise.

### Represent a published signal only once, independently of subscribers

Rejected as the sole graphical representation because it would hide the
effective collaborations between the publisher and each consuming
participant.

A future signal-centric view may be generated in addition to the
collaboration diagram, but it does not replace the pairwise
collaboration view.

## Implementation Direction

Proceed incrementally:

1. extend the `.collab` grammar to accept optional `[P/S]` on a signal
   declaration while preserving per-signal comments;
2. treat absence of the annotation as `DIRECT`;
3. add delivery mechanism to the internal route representation;
4. preserve delivery metadata during signal reuse reconciliation;
5. reject reuse of one signal with inconsistent delivery mechanisms;
6. render `[P/S]` beside P/S signals in generated PlantUML;
7. extend tests to cover single and multiple subscribers;
8. extend signal generation to group P/S signals before `MAX_PUB_SIG`;
9. generate `MAX_PUB_SIG` and retain `MAX_APP_SIG`;
10. later extend the QM reader and model checker to reconcile declared
    P/S relationships with executable subscription/publication
    behaviour.

The **Fly 'n' Shoot** example described by Samek should be considered a
valuable future validation case because it contains multiple
collaborating Active Objects and non-trivial use of publish/subscribe
semantics.

It can test whether the notation and tooling remain clear and useful
when applied to an application not designed specifically around
`collab`.

## Emerging Principle

> **A collaboration describes semantic communication between system
> participants; the delivery mechanism describes how that communication
> is realised.**

Therefore:

> **Direct posting is the default collaboration delivery mechanism.
> Publish/subscribe is represented by the same signal route annotated
> `[P/S]`.**

And:

> **One published signal may establish many effective collaboration
> routes while remaining one application signal.**

This preserves the simplicity of the collaboration model while making
the QP delivery semantics required for generation, analysis, and
verification explicit.

