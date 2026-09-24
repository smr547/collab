# ADR-0009: Preserve the Simplicity of Collaboration Diagrams

- **Status:** Proposed
- **Date:** 2026-09-24
- **Project:** collab
- **Related:** ADR-0001 — Establish `collab` as a Textual Collaboration Modelling Language
- **Related:** ADR-0007 — Model Event Delivery Mechanism in Collaborations
- **Related:** ADR-0008 — Introduce a Formal Semantic Model for Collaborations and Event Delivery
- **Semantic model:** `docs/diagrams/collab-semantic-model-draft-3.puml`

## Context

The collaboration language began as a concise description of participants, their relationships, and the signals they exchange. ADR-0008 subsequently established a richer semantic model separating design-time Participant, Collaboration, Route and Signal from runtime Event, Generation, Injection and Delivery. It identifies POST, PUBLISH and DISPATCH as injection mechanisms and accommodates participants other than Active Objects, including passive HSMs, ISRs and timers.

Discussion of the Rain Gauge and Samek's Fly 'n' Shoot confirms the usefulness of that model. A passive Mine HSM can receive synchronous dispatch from Tunnel; a timer can originate a meaningful event; and publish/subscribe differs from direct posting. Yet displaying every semantic distinction risks making the primary collaboration diagram crowded and less useful.

The semantic model and its graphical presentation have different purposes. A complete semantic foundation need not yield an exhaustive diagram.

## Decision

**Retain Semantic Model Draft 3 as the foundation for further development without changing it as a result of this discussion. Deliberately keep the primary collaboration diagram a selective, readable architectural view.**

The primary diagram should communicate the participants, their collaboration relationships, communication direction and exchanged semantic signals. Additional detail should appear only when it materially improves understanding.

The presence of information in the semantic model does not, by itself, justify displaying it. Information may remain available to validation, code generation or other derived views without appearing in the primary diagram.

The diagram is not a runtime event trace or an exhaustive depiction of QP machinery.

## Participant Scope

Participation is determined by involvement in event communication, not by inheritance from `QActive`. Passive HSMs, ISRs and timers may therefore be legitimate participants.

A passive Mine may appear without depicting Tunnel's ownership of its instances. A timer may appear as an event source without depicting creation, arming, disarming or state-dependent lifecycle. These are implementation and behavioural concerns rather than mandatory collaboration-diagram content.

## Delivery Semantics

ADR-0008's POST, PUBLISH and DISPATCH distinctions remain part of the semantic foundation. ISR context is not a fourth injection mechanism; it describes the context from which an event is injected.

Where a delivery distinction materially affects interpretation, a concise annotation may be appropriate. This ADR does not prescribe new syntax, arrow styles, an event bus, or a depiction of framework infrastructure.

ADR-0007's initial route-level delivery rules and ADR-0008's later distinction between Signal, Injection, Delivery and Route must be reconciled when the language changes are designed. In particular, a signal's semantic identity need not imply one immutable injection mechanism on every route.

## Temporal Participants

Timers are potentially useful collaboration participants. Their purpose and human-readable cadence can clarify a system's architecture: for example, a Rain Gauge inactivity interval or periodic health-report requirement, or Fly 'n' Shoot's recurring game clock.

The diagram must not duplicate the timer's behavioural implementation in QM. The grammar for timer declarations, optional cadence documentation and PlantUML appearance are deferred to a subsequent decision.

## Relationship to QM

`collab` describes system-level communication contracts; QM owns internal HSM behaviour, states, transitions and actions. The primary collaboration diagram complements, rather than reproduces, the individual HSM diagrams.

## Validation Against Applications

The Rain Gauge remains the working application. A separate Fly 'n' Shoot `.collab` example is a valuable independent test of temporal events, publish/subscribe, Active Objects and synchronous dispatch to passive HSMs.

The example should test whether the collaboration view adds architectural understanding without forcing every application detail into one diagram.

## Complete Signal Inventory and Local Elaboration

The collaboration source is the authoritative inventory of application signals, including signals used entirely within one HSM. Locality does not remove a signal from generation, validation or documentation. The primary diagram may omit or compactly render local interactions without changing the underlying model.

A reflexive route expresses a local use with the existing collaboration grammar, for example:

```text
object_A --> object_A : CONTINUE  // used internally to implement transitory states in the HSM
```

No separate local-signal grammar or mandatory `local` keyword is required for this use case. A future standalone signal declaration may be considered if a concrete need arises; it is not a prerequisite for the current design.

Signal identity is independent of route and receiver context. A ubiquitous signal such as `CONTINUE` may be reused by multiple AOs for different purposes. The receiving object and its HSM state establish the context. The generator emits one `CONTINUE_SIG` enumerator, not one per AO; the validator checks each declared receiving route against its own HSM.

Comments attached to routes are part of the specification, not disposable diagram annotations. Generation must preserve their contextual meaning. When one signal appears on several routes, aggregate **all** associated route descriptions in the generated enum source, identifying the relevant source and receiver rather than selecting one description as the signal's universal meaning. Preserve them in derived documentation as well. For example:

```cpp
// Control -> Control: advance through transitory states.
// Radio -> Radio: continue transmission processing.
CONTINUE_SIG,
```

The collaboration source may be elaborated incrementally: a system architect defines principal participants and communication contracts; a developer adds local signals, reflexive routes, timers and contextual explanations as the HSM design develops. Both use the same complete specification. Generation and validation consume the elaborated model, while the primary diagram remains a selective architectural view.

Generate one authoritative application signal enumeration from that complete inventory. QM-generated code shall use it rather than maintain a competing independently ordered enumeration. Framework-reserved signals remain distinct. The Rain Gauge build failure caused by `CONSIDER_SLEEPING_SIG` being present in the Collab-generated header but absent from the QM-owned enumeration demonstrates why this matters.

## Timers as Behavioural Contracts

Timers are first-class collaborators, including timers local to an individual HSM. Their cadence, purpose, event route and receiver can express application requirements valuable to architects, developers and testers. For example, the Rain Gauge SleepTimer describes a periodic opportunity for Control to consider deep sleep after an inactivity interval.

Documentation must distinguish a timer's event-generation contract from conditional downstream behaviour: a periodic `CONSIDER_SLEEPING` event does not guarantee that the device sleeps exactly 30 seconds later when workers remain busy.

A primary diagram may represent local timers as compact clock annotations or omit their detailed routes when they crowd out principal collaborators. A detailed view and generated textual documentation can expose the complete temporal contract. Rendering choices must not suppress validation, signal generation or documentation. Timer implementation and lifecycle remain in QM; cross-model checks can establish agreement without reproducing the HSM in the collaboration diagram.

Structured cadence and purpose metadata, compact timer rendering, and detailed diagram modes are implementation design work, not changes to Semantic Model Draft 3 mandated by this ADR.

## Consequences

The complete collaboration specification supports authoritative signal generation, contextual comment preservation, richer validation and derived artefacts while the primary diagram remains legible. Some information will necessarily require inspection of the source, HSM models or another view. This trade-off is accepted.

Proposed extensions must demonstrate their value to the reader rather than merely their availability in the semantic model.

## Deferred Decisions

- Passive HSM declaration and rendering.
- Concise synchronous-dispatch notation.
- Refinement of timer cadence/purpose metadata, compact rendering and detailed views.
- Reconciliation of ADR-0007 with ADR-0008 in the language and tooling.
- Validation with a separate Fly 'n' Shoot example.

These are subsequent language and rendering decisions, not amendments to Semantic Model Draft 3.

## Principle

> **The semantic model defines what the collaboration language can understand; the collaboration diagram presents what a reader needs to see.**

The diagram communicates architecture, not all the machinery beneath it.
