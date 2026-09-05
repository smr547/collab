# ADR-0008: Introduce a Formal Semantic Model for Collaborations and Event Delivery

-   **Status:** Proposed
-   **Date:** 2026-09-06
-   **Project:** collab / HSM model tooling
-   **Related:** ADR-0003 --- Signal Reuse Across Multiple Routes
-   **Related:** ADR-0004 --- Model Completeness and Unified Signal
    Generation
-   **Related:** ADR-0006 --- Peer System Models and Model-Driven
    Toolchain
-   **Related:** ADR-0007 --- Model Event Delivery Mechanism in
    Collaborations
-   **Diagram:** `docs/diagrams/collab-semantic-model-draft-3.puml`

## Context

The original `collab` language began with a deliberately simple purpose:
describe communication between collaborating Active Objects and render
that communication as a concise PlantUML collaboration diagram.

Experience with the Rain Gauge application and subsequent analysis of
Samek's Fly 'n' Shoot example exposed a richer semantic structure
beneath that notation.

Several observations drove this refinement.

First, not every system element participating in event communication is
necessarily a QP Active Object. Events can originate in ISRs, timers,
infrastructure tasks, HSM action code, device drivers, and other
execution contexts. Passive `QHsm` instances can also participate in
event processing when an event is synchronously dispatched to them by
their owner.

Second, analysis of event delivery showed that the earlier model was
conflating several distinct concepts. An Event is generated at a
particular instant, injected into the execution environment using some
mechanism, and subsequently delivered to one or more recipients.

Third, publish/subscribe demonstrated that Event injection and Event
delivery are not the same thing. A single publication can result in
zero, one, or many deliveries, depending on subscription state at that
instant.

Fourth, collaboration topology is not wholly equivalent to runtime
connectivity. A Route may be identifiable at design time while its
availability at runtime changes. Publish/subscribe is the clearest
example: a potential publisher-to-subscriber Route exists in the design,
but it is traversable for a given Signal only while the destination is
subscribed.

Finally, attempts to formalize the previously proposed `EventFlow` class
exposed uncertainty about what independent semantic concept it
represented. Once Event, Injection, Delivery, and Route were separated,
`EventFlow` was no longer necessary in the current model.

These discoveries justify an explicit semantic metamodel rather than
allowing the meaning of `.collab` constructs to remain implicit in
parser and renderer implementation.

## Decision

Adopt a provisional formal semantic model for `collab`, represented by:

`docs/diagrams/collab-semantic-model-draft-3.puml`

The model deliberately separates two conceptual packages:

1.  **Design / Structural Model**
2.  **Runtime / Dynamic Model**

This separation is fundamental.

The structural model describes the system's possible communication
topology and event vocabulary. The runtime model describes individual
event occurrences and how those occurrences enter and traverse that
topology.

Draft 3 is a semantic checkpoint, not a declaration that the model is
complete or final.

## Design / Structural Model

### Participant

A **Participant** is an identifiable system element that can originate
and/or receive Events and therefore take part in Collaborations.

Participation is not restricted to subclasses of `QActive`.

Candidate Participant kinds currently include Active Objects, passive
HSMs, ISRs, device drivers, timers, tasks or threads, and other
event-generating or event-receiving system elements.

The taxonomy is intentionally provisional.

A Participant may also represent a classifier or system role having more
than one runtime instance. The semantic model therefore retains a notion
of multiplicity.

Detailed capability rules associated with Participant kinds are not
decided by this ADR.

### Collaboration

A **Collaboration** represents the relationship that two Participants
collaborate.

It is modelled as the association class of the reflexive many-to-many
relationship:

``` text
Participant collaborates with Participant
```

The Collaboration itself is not directional.

For two Participants `P1` and `P2`:

``` text
Collaboration(P1,P2) = Collaboration(P2,P1)
```

A Collaboration can be binary or reflexive. The distinction is currently
derived from the participating endpoints rather than represented by
separate subclasses.

### Route

A **Route** is a directional architectural path from an origin
Participant to a destination Participant through which Events may be
delivered.

Direction is intrinsic to Route identity:

``` text
Route(P1 -> P2) != Route(P2 -> P1)
```

A Collaboration comprises one or more Routes.

A binary Collaboration may contain Routes in one direction or both
directions. A reflexive Collaboration can contain a Route whose origin
and destination are the same Participant.

A Route belongs to the design-time possibility topology. The existence
of a Route in the model does not necessarily imply that it is
continuously available at runtime.

### Signal

A **Signal** identifies the semantic type of an Event.

Signals belong to the design-time vocabulary of the application.
Individual Event occurrences are typed by exactly one Signal.

The same Signal may participate in more than one Route. Signal identity
is therefore independent of Route identity.

## Runtime / Dynamic Model

### Event

An **Event** is a single runtime occurrence generated by a Participant
at an instant in time.

An Event has exactly one Signal identifying its semantic type, a
generation time, and zero or more parameters.

For example, `TIME_TICK` is a Signal. Successive ticks are distinct
Events carrying that Signal.

This ADR adopts the conceptual interpretation that a published Event
remains a single Event occurrence even when publication results in
delivery to multiple subscribers.

This deliberately separates semantic Event identity from implementation
details concerning event objects, references, queues, or memory
management inside QP.

### Generation

**Generation** is the occurrence by which a Participant creates an
Event.

Candidate event-generating Participants include ISRs responding to
external stimuli, polling tasks detecting conditions, timers expiring,
and HSM action code executing in response to earlier Events.

Generation and delivery are distinct concepts.

### Injection

**Injection** describes how a generated Event enters the event-delivery
mechanism.

The currently identified injection mechanisms are:

``` text
POST
PUBLISH
DISPATCH
```

#### POST

POST targets the event queue of a particular Active Object.

The queueing discipline may be:

``` text
FIFO
LIFO
```

FIFO and LIFO are therefore treated as properties of POST rather than
independent top-level mechanisms.

POST identifies a particular receiver at injection time and consequently
selects a specific Route.

#### PUBLISH

PUBLISH injects an Event without naming an individual receiver.

The set of deliveries is determined by the subscription state associated
with the Event's Signal at runtime.

A publication can therefore result in:

``` text
0..* Deliveries
```

A single published Event can traverse multiple Routes.

#### DISPATCH

DISPATCH synchronously supplies an Event to a passive HSM in the context
of the current run-to-completion execution.

It does not enqueue the Event for later independent processing.

DISPATCH identifies the destination and therefore selects a specific
Route.

### Delivery

A **Delivery** is one runtime arrival of an Event at a receiving
Participant.

Each Delivery traverses exactly one Route.

This distinction is especially important for publish/subscribe:

``` text
one Event
    -> one PUBLISH Injection
        -> zero, one, or many Deliveries
            -> zero, one, or many Routes traversed
```

POST and DISPATCH normally result in one Delivery to their explicitly
identified destination.

The exact failure semantics of an attempted injection or delivery are
outside the scope of this ADR.

## Structural and Runtime Relationship

The model intentionally connects the two packages at specific semantic
points.

An Event is typed by a design-time Signal. An Event is generated by a
Participant. A Delivery traverses a design-time Route. A Delivery
terminates at a receiving Participant.

This permits the static model to describe what communication is
architecturally possible while the runtime model describes what actually
occurs during execution.

## Route Existence and Runtime Availability

A Route is a design-time architectural possibility.

Route availability may be state-dependent at runtime.

Publish/subscribe provides the immediate example. A design may identify
a publisher-to-subscriber Route as possible for a particular Signal,
while an actual delivery can occur only while the destination is
subscribed to that Signal.

This ADR therefore distinguishes **Route existence** from **Route
availability**.

The former belongs to the structural model. The latter is a runtime
property or derived condition.

The precise representation of route availability, subscription state,
and Signal-specific route permissions remains open.

The collaboration diagram should initially be understood as describing a
**possibility topology**, not a snapshot of currently active runtime
communication.

## EventFlow

The `EventFlow` abstraction introduced in an earlier semantic-model
draft is removed from Draft 3.

The earlier concept attempted to combine a Signal, a Route, and a
delivery mechanism.

Subsequent analysis showed that these concerns cross the boundary
between structural and runtime semantics.

At present there is no sufficiently precise independent definition of
`EventFlow` to justify retaining it as a first-class metamodel element.

This does not preclude a future concept representing a design-time
permission for a particular Signal to use a particular Route. Such a
concept should be introduced only when its semantics are clearly
defined.

## Relationship to ADR-0007

ADR-0007 introduced delivery mechanism as a property associated with
signal routes and deliberately prohibited use of one semantic Signal
with different delivery mechanisms on different routes.

Analysis of Fly 'n' Shoot has challenged that simplifying assumption.

In particular, a Signal such as `TIME_TICK` may be delivered to an
Active Object using publish/subscribe and subsequently synchronously
dispatched to a passive HSM.

Draft 3 therefore separates Signal identity, Injection, Delivery, and
Route rather than assigning one immutable delivery mechanism to a
Signal.

This ADR does not retrospectively modify ADR-0007. ADR-0007 remains part
of the design history and records the earlier conservative decision.

The exact `.collab` language changes required by this refinement will be
decided separately after the semantic model has been exercised further.

## Implications for Collaboration Diagrams

The system collaboration diagram remains primarily a structural view.

Its purpose is to communicate which Participants exist, which
Participants collaborate, the directional Routes between them, which
Signals are intended to participate in those communication
relationships, and relevant delivery semantics where useful.

The diagram is not intended to become a runtime trace.

Self-directed Routes can exist in the semantic model, but whether
reflexive Collaborations or self-events should normally appear in the
system-level collaboration diagram remains undecided.

Likewise, runtime subscription changes should not require the base
diagram to redraw itself. A future runtime or trace-derived view may
show actual route traversal or availability.

## Implications for QSPY and Runtime Verification

Separating the structural model from runtime Event, Injection, and
Delivery concepts creates a potential future relationship with QSPY
traces.

Conceptually:

``` text
system.collab
    -> possible communication topology

QSPY trace
    -> observed runtime Events and Deliveries

model/trace analysis
    -> compare expected and observed communication
```

Possible future tooling could identify Routes exercised during a test,
modelled Routes never observed, observed deliveries not permitted by the
model, P/S subscriber relationships active during execution, and event
sequences associated with particular use cases.

No QSPY integration is required by this ADR.

## Consequences

### Positive

-   the semantic model is no longer restricted to Active Objects;
-   structural and runtime concepts are explicitly separated;
-   Event identity is distinguished from Signal identity;
-   Generation, Injection, and Delivery are distinguished;
-   publish/subscribe fan-out is represented naturally;
-   Route becomes a precise directional architectural concept;
-   dynamic Route availability can be discussed without making the
    collaboration diagram itself a runtime trace;
-   FIFO and LIFO become properties of POST rather than unrelated
    delivery types;
-   passive HSM dispatch fits naturally into the model;
-   `EventFlow` is removed until a precise need and definition exist;
-   the model provides a stronger foundation for future DSL,
    model-checking, QM, STT, and QSPY tooling.

### Costs and Risks

-   the semantic model is more sophisticated than the original `collab`
    implementation;
-   several concepts remain provisional;
-   the current DSL does not yet express the complete metamodel;
-   Participant kinds and capabilities require further investigation;
-   Signal-to-Route permissions are not yet formally represented;
-   Route availability introduces temporal considerations that require
    care;
-   some statements about QP execution semantics require continued
    validation against QP documentation and real applications.

## Open Questions

Draft 3 intentionally leaves the following unresolved:

1.  What is the final taxonomy of Participant kinds?
2.  Should Participant capabilities be modelled explicitly or derived
    from kind?
3.  Which Participant kinds may generate, receive, subscribe, publish,
    post, or dispatch Events?
4.  How should the design-time relationship between Signal and Route be
    represented?
5.  Does that relationship deserve its own named metamodel element?
6.  How should runtime subscription and Route availability be
    represented, if at all?
7.  Should reflexive Collaborations and self-events appear in the system
    collaboration diagram or only in AO/HSM-centric derived views?
8.  Is the one-Event/one-Injection cardinality universally correct?
9.  Are there additional QP injection or delivery mechanisms that must
    be represented?
10. How should Participant multiplicity interact with Route identity and
    instance-specific communication?
11. What `.collab` syntax best expresses the eventual semantic model
    without sacrificing readability?

These questions should be answered by further analysis of QP
applications and by exercising the model against both the Rain Gauge and
Fly 'n' Shoot examples.

## Documentation Direction

Three complementary artefacts should be maintained.

### ADR-0008

Records why the formal semantic structure was introduced and which
conceptual decisions were made at this checkpoint.

### `docs/diagrams/collab-semantic-model-draft-3.puml`

Provides the graphical metamodel corresponding to this ADR.

### `docs/collab-semantic-model.md`

A future living document that will define the current semantics of the
`collab` language and metamodel in detail.

The ADR is historical. The diagram is structural. The semantic-model
document will become the evolving specification.

## Emerging Principles

> **Participation in a Collaboration is determined by involvement in
> Event communication, not by membership in the Active Object class
> hierarchy.**

> **A Collaboration is not directional; its Routes are.**

> **A Route describes a design-time communication possibility. A
> Delivery is a runtime traversal of that Route.**

> **A Signal identifies an Event type; an Event is one runtime
> occurrence of that type.**

> **Generation, Injection, and Delivery are distinct semantic
> concepts.**

> **One published Event may result in zero, one, or many Deliveries of
> that same Event.**

> **The collaboration model describes possible communication topology;
> runtime state determines which possibilities are available and which
> are actually exercised.**

These principles form the conceptual basis of Semantic Model Draft 3 and
will guide subsequent evolution of the `collab` language and tooling.
