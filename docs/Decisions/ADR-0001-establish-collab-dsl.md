# ADR-0001: Establish `collab` as a Textual Collaboration Modelling Language

- **Status:** Accepted
- **Date:** 2026-08-17
- **Project:** collab

## Context

`collab` emerged while designing an embedded Rain Gauge / Weather Station using the Quantum Leaps QP framework and QM modelling tool.

The system is being decomposed into collaborating Active Objects (AOs). QM is an excellent tool for describing the internal hierarchical state machine (HSM) behaviour of an individual AO and for generating the corresponding C++ implementation.

A different modelling problem exists at the system level: describing how the AOs collaborate.

In particular, the system design needs an authoritative description of:

- the Active Objects participating in the system;
- which pairs of Active Objects collaborate;
- the direction of communication between them; and
- the domain signals exchanged across each collaboration.

During the Rain Gauge design, PlantUML was initially selected as a text-based way of drawing these collaborations. This was attractive because PlantUML source is human-readable, version-controllable, and machine-processable.

However, a useful distinction emerged between the **semantics of the collaboration model** and its **graphical rendering**.

Our preferred collaboration notation has the following semantics:

1. A pair of collaborating AOs has one collaboration relationship.
2. That collaboration is represented graphically by one solid line.
3. Signals travelling in the same direction are grouped together.
4. Arrowheads on the collaboration line summarise the direction or directions in which signals travel.
5. Where no signals travel in one direction, no arrowhead is shown in that direction.
6. Signal direction is authoritative; graphical arrowheads are derived from it rather than specified independently.
7. Straight lines and 90-degree bends are preferred in the rendered diagram.

This led to a more important observation: PlantUML is fundamentally a rendering language, while the information being captured is a small system model with its own semantics and validation rules.

At the same time, the domain signal vocabulary is required by the C++/QP implementation. Maintaining the collaboration diagram, the signal catalogue, and the C++ signal enum independently would introduce unnecessary duplication and opportunities for inconsistency.

The emerging principle is:

> **State machines describe behaviour within an object. Signals describe contracts between objects.**

The collaboration model should therefore own the inter-object communication contract, while QM should continue to own the internal behavioural model of each AO.

## Decision

Create `collab` as a small, textual domain-specific language (DSL) for modelling collaborations between Active Objects.

A `.collab` file is the **authoritative source** for:

- participating Active Objects;
- collaboration relationships between pairs of Active Objects;
- directional signal groups; and
- the inter-AO domain signal vocabulary.

PlantUML is a **generated view** of that model rather than the authoritative source.

The initial compiler, `collabc`, will:

1. parse a `.collab` source file;
2. validate its syntax and selected modelling conventions;
3. derive collaboration arrowheads from the declared signal directions;
4. generate PlantUML for rendering the collaboration diagram; and
5. generate a QP-compatible C++ signal enumeration.

Conceptually:

```text
                    .collab
              authoritative model
                     |
          +----------+-----------+
          |          |           |
          v          v           v
       validate   PlantUML   C++ signals
                    |           |
                    v           v
                SVG / PNG     QP / QM
```

The generated artefacts are derived products and should not be edited as independent sources of design information.

## Initial Language Model

Version 1 of the language deliberately contains only a few concepts.

For example:

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

This declares two Active Objects and one collaboration.

The four signals form a single directional group from `BucketSensorAO` to `ControlAO`.

From that semantic information the compiler can derive a single-ended collaboration arrow in PlantUML and a C++ signal catalogue.

If signals are later declared in the opposite direction within the same collaboration, the generated diagram becomes bidirectional without requiring a separately maintained graphical declaration.

## Collaboration Diagram House Style

The following conventions form part of the initial design.

### One collaboration per AO pair

The number of graphical relationships should reflect the number of collaborating object pairs, not the number of individual signals.

Ten signals exchanged between two AOs still constitute one collaboration.

### Signals grouped by direction

Signals travelling from one participant to the other are presented as a group.

A bidirectional collaboration therefore has two directional groups, not a collection of independent signal arrows.

### Direction derived from signal declarations

Arrowheads are generated from the directional signal groups.

They are not separately specified because doing so would create two sources of truth.

### Sender identity preserved in signal names

Where appropriate, status and fault signals should preserve enough domain or sender identity to remain unambiguous as the system grows.

For example:

```text
BUCKET_SENSOR_BUSY
BUCKET_SENSOR_IDLE
```

are preferred to:

```text
SENSOR_BUSY
SENSOR_IDLE
```

The compiler may report departures from such house conventions where they can be checked reliably.

### Orthogonal rendering preferred

Generated PlantUML should request straight lines and 90-degree bends where practical.

This is a rendering convention, not part of the semantic model.

## Relationship to QM

`collab` does not replace QM.

The two tools operate at complementary modelling levels.

```text
collab
    collaboration between objects
    communication contracts
    domain signals
        |
        v
    generated signal declarations

QM
    behaviour within an object
    HSM states and transitions
    actions
        |
        v
    generated behavioural C++
```

QM remains authoritative for:

- HSM states;
- transitions;
- entry and exit actions;
- state-local behaviour; and
- generated HSM implementation.

`collab` is authoritative for the communication vocabulary crossing AO boundaries.

The generated C++ signal catalogue provides a bridge between the system collaboration model and the individual behavioural models.

## Validation

The compiler is not merely a renderer.

It should reject structurally inconsistent models and report departures from selected project conventions.

The initial implementation validates such things as:

- legal AO names;
- duplicate AO declarations;
- references to undeclared AOs;
- duplicate collaborations between the same pair of AOs;
- invalid collaboration endpoints;
- duplicate directional groups;
- collaborations without signal flows;
- signal groups without signals;
- invalid signal naming; and
- duplicate signal declarations.

Warnings may additionally identify house-convention issues that are undesirable but not structurally invalid.

A strict mode may treat such warnings as errors.

This makes `collab` a small model checker as well as a translator.

## Generated C++ Signals

The initial C++ target is a QP-compatible signal enumeration.

For example, the Rain Gauge collaboration can generate an artefact of the form:

```cpp
enum AppSignals {
    BUCKET_TIPPED_SIG = QP::Q_USER_SIG,
    BUCKET_SENSOR_BUSY_SIG,
    BUCKET_SENSOR_IDLE_SIG,
    RAIN_BUCKET_FAULT_SIG,

    MAX_APP_SIG
};
```

The `.collab` source, rather than this generated enum, remains authoritative.

The first implementation intentionally limits code generation to the signal catalogue.

## Deliberate Limits

Version 1 does not attempt to model:

- event payload types;
- publish/subscribe versus direct posting;
- priorities;
- AO deployment to processors or cores;
- HSM states;
- timers;
- synchronous calls;
- inheritance;
- multiplicities; or
- generated event classes.

These features should not be added speculatively.

The language will be extended when concrete applications demonstrate a modelling requirement.

The guiding principle is:

> **Keep the collaboration model semantic, readable, and smaller than the implementation it generates.**

## Rationale

### Separate semantics from rendering

PlantUML is valuable for producing diagrams, but the collaboration model has semantics independent of how those semantics are drawn.

Making `.collab` authoritative allows PlantUML to remain what it does well: rendering.

### Single source of truth

The same directional signal declarations determine:

- the communication contract;
- diagram arrowheads;
- diagram signal annotations; and
- generated C++ signal declarations.

This avoids manually synchronising several representations of the same design information.

### Human-readable models

The DSL is intentionally small enough that its source can be read as an architectural document.

For example:

```text
BucketSensorAO -> ControlAO
    BUCKET_TIPPED
    BUCKET_SENSOR_IDLE
```

requires little specialised knowledge to understand.

### Version-control friendliness

`.collab`, generated PlantUML, generated C++, QM models, Markdown documentation, and ADRs are all textual artefacts suitable for meaningful Git history and review.

### Model-driven development

The approach extends the model-driven development already provided by QM.

Rather than treating diagrams as documentation reconstructed after implementation, the architecture itself becomes capable of generating implementation artefacts.

## Consequences

### Positive

- System collaboration has an explicit textual model.
- Inter-AO signals have one authoritative source.
- Collaboration diagrams are generated rather than manually synchronised.
- Graphical direction cannot silently disagree with declared signal direction.
- C++ signal declarations can be generated from architectural intent.
- Project-specific modelling conventions can be checked automatically.
- The DSL is independent of the Rain Gauge application and can be reused.
- The design can evolve through normal Git commits and ADRs.

### Costs and risks

- A language and compiler now need to be maintained.
- Language evolution requires discipline and, eventually, compatibility rules.
- There is a risk of adding implementation detail until the DSL becomes unnecessarily complicated.
- PlantUML layout remains partly dependent on the renderer and may not always produce the preferred graphical arrangement.
- The first C++ generator is QP-oriented even though the underlying collaboration model is more general.

These risks are accepted, with a deliberate bias toward keeping the language small.

## Alternatives Considered

### Use PlantUML directly as the authoritative source

This was the initial approach.

It was superseded because our collaboration semantics and validation rules were becoming distinct from PlantUML's role as a drawing language. Encoding increasingly specialised semantics in PlantUML would couple the model unnecessarily to its renderer.

### Maintain the signal enum manually

Rejected as the preferred approach because it duplicates information already present in the collaboration model and creates another synchronisation point.

### Generate diagrams from C++ implementation

Rejected because it reverses the desired direction of authority. Architecture should express communication intent; implementation artefacts should be derived from that intent where practical.

### Put the collaboration language inside the Rain Gauge or `qp-lab` repository

Rejected once the concept became clearly reusable beyond the application that caused its discovery.

`collab` has its own language, compiler, documentation, tests, examples, and design decisions and therefore warrants an independent repository.

## Repository Scope

The `collab` repository owns:

- the `.collab` language definition;
- the compiler/translator;
- validation rules;
- generated-target support;
- examples;
- tests; and
- ADRs concerning the language and compiler.

Applications such as the Rain Gauge consume `collab`; they do not define it.

The Rain Gauge remains an important example and the first real application driving language evolution.

## Future Evolution

Future extensions should be driven by concrete modelling pressure from real systems.

Each significant semantic extension should be considered explicitly and, where appropriate, recorded in an ADR.

Likely areas of investigation include event payloads and richer generated communication contracts, but none are committed by this decision.

Backward compatibility and explicit language versioning should become formal concerns when the first incompatible language change is proposed.

## Summary

`collab` is established as an independent textual modelling language and compiler for Active Object collaboration.

Its central architectural separation is:

> **`.collab` describes communication between objects; QM describes behaviour within objects.**

The `.collab` source is authoritative. PlantUML diagrams and C++ signal declarations are generated from it.

The language will remain deliberately small and will grow in response to demonstrated modelling needs rather than speculative features.
