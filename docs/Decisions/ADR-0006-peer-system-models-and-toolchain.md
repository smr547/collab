# ADR-0006: Establish the Peer System Models and Model-Driven Toolchain

-   **Status:** Accepted
-   **Date:** 2026-08-19
-   **Project:** collab / HSM model tooling
-   **Related:** ADR-0004 --- Model Completeness and Unified Signal
    Generation
-   **Related:** ADR-0005 --- State Transition Tables and
    Transition-Cell Completeness
-   **Diagram:** `doc/diagrams/model-toolchain.puml`

## Context

Experience developing the Rain Gauge collaboration model and
`BucketSensorAO` HSM has expanded the scope of `collab` beyond
collaboration-diagram and signal-enum generation.

ADR-0004 established **model completeness** and decided that the
application signal catalogue should be derived by reconciling the
complete system collaboration model with behavioural models rather than
by duplicating AO-local signals in `.collab`.

ADR-0005 extended the completeness idea inside an HSM by introducing
State Transition Tables (STTs) and explicit classification of otherwise
undefined state/event combinations.

Drawing the complete toolchain exposed a further architectural point: a
QM file is not naturally a model of one AO. A single QM application
model can contain multiple Active Objects and their HSMs, together with
other application artefacts that may be useful to future analysis
tooling.

The application therefore has two peer authoritative model artefacts:

``` text
system.collab                 system.qm
```

They describe complementary aspects of the same application.

The reference architecture for this decision is shown in
`doc/diagrams/model-toolchain.puml`.

## Decision

The `collab` project shall treat `system.collab` and `system.qm` as
**peer authoritative system models** with complementary
responsibilities.

Neither model shall duplicate information merely to make another tool
easier to implement. Their information shall instead be reconciled
through model readers and a shared semantic representation from which
analysis reports and generated artefacts can be derived.

Conceptually:

``` text
                    APPLICATION MODEL

          system.collab       system.qm
                |                 |
                +--------+--------+
                         |
                         v
                  model analysis
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
      signals.hpp       STTs        diagnostics
```

## Authority of `system.collab`

`system.collab` is authoritative for the system's **participation and
communication structure**.

It defines:

-   the complete set of system participants;
-   participant kinds, such as Active Objects and ISRs;
-   collaborations between participants;
-   direction of communication;
-   inter-participant signal identities;
-   permitted routes by which those signals travel.

Because the collaboration model is complete, it also acts as a system
manifest. Tooling can use it to determine which behavioural participants
should have corresponding HSM definitions.

For example, an AO declared in `system.collab` should normally have an
HSM in `system.qm`, while an ISR need not.

## Authority of `system.qm`

`system.qm` is authoritative for the application's **executable
behaviour**.

A single `system.qm` may contain:

-   multiple Active Object specifications;
-   one HSM for each behavioural AO;
-   states and state hierarchy;
-   transitions;
-   guards;
-   entry, exit, and transition actions;
-   time-event usage;
-   other QM model artefacts;
-   information required for generation of executable C++.

The tooling shall not assume that a QM file corresponds to a single AO.

For the Rain Gauge application, for example:

``` text
system.qm
    |
    +-- BucketSensorAO HSM
    +-- ControlAO HSM
    +-- RadioAO HSM
    +-- other QM artefacts
```

Future tooling should preserve access to the complete QM model rather
than extracting only the information currently known to be useful.

## Peer Models, Not Competing Models

`system.collab` and `system.qm` describe different dimensions of the
same application.

Their authority can be summarised as:

> **`system.collab` is authoritative for system structure and
> communication.**

> **`system.qm` is authoritative for executable application behaviour.**

The two models are peers, but their contents are not expected to be
identical.

Where their concerns overlap, tooling should establish explicit
cross-model invariants and report inconsistencies rather than silently
choosing one model over the other.

Examples include:

-   every AO declared by the complete collaboration model should have
    corresponding behavioural definition in `system.qm`;
-   inter-participant signals consumed by an AO should be consistent
    with routes declared in `system.collab`;
-   signal identities should be reconciled into one application-wide
    vocabulary.

## Per-AO PlantUML HSMs

Files such as:

``` text
BucketSensorAO.puml
ControlAO.puml
RadioAO.puml
```

are useful because PlantUML is textual, diff-friendly, human-readable,
and convenient for design discussion.

During early design an AO `.puml` file may be hand-authored as an
electronic pencil-and-paper sketch.

However, once that HSM has been incorporated into `system.qm`, the QM
model becomes authoritative for executable behaviour. At that point the
AO PlantUML HSM should normally become a **derived view**:

``` text
system.qm
    |
    v
qm2puml
    |
    +-- BucketSensorAO.puml
    +-- ControlAO.puml
    +-- RadioAO.puml
```

This avoids maintaining two competing behavioural authorities.

The generated `.puml` files remain valuable for documentation, design
review, human discussion, rendering, and analysis.

## QM-to-PlantUML Extraction

A `qm2puml` tool is part of the intended toolchain.

Its purpose is to extract one or more AO HSM views from the system-level
QM model:

``` text
system.qm
    |
    +-- qm2puml --> BucketSensorAO.puml
    |             ControlAO.puml
    |             RadioAO.puml
    |
    +-- QM ------> generated C++
```

The extracted PlantUML is derived documentation and analysis material,
not a replacement executable model.

## Direct QM Model Reading

Although `qm2puml` is useful, future model-analysis tooling should
preferably be capable of reading `system.qm` directly.

The preferred high-integrity path is:

``` text
system.qm
    |
    v
QM reader
    |
    v
common semantic model
```

rather than requiring conversion through per-AO PlantUML as an
obligatory analysis path.

Direct QM reading avoids throwing away information that exists in the QM
model but is not represented in the extracted HSM diagram. The QM XML
may contain application information beyond HSM topology that later
proves useful.

## Common Semantic Model

The toolchain should evolve toward shared model readers feeding a common
semantic representation:

``` text
.collab reader ------+
                     |
QM reader -----------+--> Common Semantic Model
                     |            |
PlantUML HSM reader -+            +--> signal generation
                                  +--> STT analysis
                                  +--> model checking
                                  +--> reports
```

The PlantUML HSM reader remains useful for early hand-authored HSMs and
derived HSM views.

The common semantic model is an architectural direction, not a
requirement to build a large framework before individual tools can
progress. The important requirement is that tools should not
independently develop incompatible interpretations of the same
application models.

## Tool Responsibilities

### `collabc`

Consumes `system.collab`.

Responsibilities:

-   parse and validate the collaboration model;
-   enforce collaboration-language rules and house conventions;
-   generate the collaboration PlantUML representation.

A derived artefact is `system-collaboration.puml`, which PlantUML can
render to SVG or other graphical formats.

### PlantUML

Consumes generated or hand-authored `.puml` files and produces rendered
diagrams.

PlantUML is a rendering and textual-diagram tool, not an authoritative
application model once the corresponding information resides in
`system.qm` or `system.collab`.

### QM

Consumes `system.qm` and generates the executable C++ representation of
the application HSMs.

This direct code-generation capability is a principal reason for
retaining QM as the behavioural authority.

### `qm2puml`

Consumes `system.qm` and extracts one PlantUML HSM view per AO.

The output is derived documentation and analysis material.

### Signal integration / enum generator

Consumes the complete collaboration model and behavioural model
information.

Responsibilities include:

-   reconcile inter-participant and AO-local signals;
-   identify missing behavioural artefacts;
-   identify inconsistencies between system communication and HSM signal
    usage;
-   construct the unified application signal catalogue;
-   generate the deterministic C++ `AppSignals` enum.

A derived artefact is `signals.hpp`. The exact command name remains an
implementation decision; `signalgen` is a working name.

### STT generator / checker

Consumes behavioural model information together with the AO's relevant
event vocabulary.

Responsibilities include:

-   construct the state/event matrix;
-   identify defined and inherited handling;
-   expose undefined state/event combinations;
-   apply and preserve engineer-authored classifications;
-   report `UNCLASSIFIED` cells;
-   assess transition-cell completeness.

The exact representation remains subject to implementation experience.

### Model checker

A general model-consistency function is expected to emerge from the
shared semantic model.

Potential checks include:

-   all required AOs have HSM definitions;
-   no unexpected behavioural models exist outside the system manifest;
-   routed signals are compatible with receiver HSMs;
-   externally consumed HSM signals have valid collaboration routes;
-   signal identities are used consistently;
-   STT classifications are complete;
-   cross-model invariants hold.

This capability may initially live inside the signal and STT tools
rather than as a separate executable. `modelcheck` is therefore a
conceptual responsibility rather than a command mandated by this ADR.

## Derived Artefacts

The two peer authoritative system models can ultimately generate or
support generation of:

``` text
system.collab
    |
    +--> system-collaboration.puml
           |
           +--> system-collaboration.svg

system.qm
    |
    +--> generated C++
    |
    +--> BucketSensorAO.puml
    +--> ControlAO.puml
    +--> RadioAO.puml
           |
           +--> AO HSM SVGs

system.collab + system.qm
    |
    +--> signals.hpp
    +--> State Transition Tables
    +--> model-completeness reports
    +--> cross-model consistency reports
```

These artefacts are reproducible products of the authoritative models
and associated engineer classifications.

## Relationship to ADR-0004

ADR-0004 established that the unified application signal catalogue must
be derived from the complete system and behavioural models rather than
maintained independently.

This ADR establishes the larger architecture in which that decision
operates. ADR-0004's behavioural model should ultimately be understood
as the AO HSM information contained in the peer `system.qm` model.

PlantUML HSM files can serve as early design representations and derived
views, but need not become permanent peer authorities.

## Relationship to ADR-0005

ADR-0005 established STT generation and transition-cell classification
as a behavioural completeness technique.

This ADR places that tooling downstream of the common semantic
understanding of `system.qm` and `system.collab`.

The STT is therefore another derived analytical view of the
authoritative application models rather than an independent description
of executable behaviour. Engineer-authored classifications of undefined
cells remain intentional analysis metadata.

## Reference Architecture Diagram

The architecture described by this ADR is represented by:

``` text
doc/diagrams/model-toolchain.puml
```

The diagram should show:

-   `system.collab` and `system.qm` as peer authoritative system models;
-   multiple AO HSMs contained within `system.qm`;
-   the `.collab` and QM model readers;
-   the common semantic model;
-   `collabc`;
-   QM;
-   `qm2puml`;
-   PlantUML;
-   signal/enum generation;
-   STT generation/checking;
-   model consistency checking;
-   generated C++;
-   generated per-AO HSM PlantUML views;
-   rendered diagrams;
-   unified signal definitions;
-   STTs and completeness/consistency reports.

The diagram is intended to evolve with the architecture. Material
changes to model authority or tool responsibility should be captured by
a subsequent ADR rather than silently changing the meaning of this
decision.

## Rationale

### Preserve clear authority

The architecture avoids having `.collab`, `.qm`, and `.puml` files
independently claim authority over overlapping information.

### Exploit QM's real scope

A QM file is an application model containing multiple behavioural
objects, not merely a serialization format for one HSM. Treating
`system.qm` at application scope exposes more useful information to
future tooling.

### Preserve information

Direct QM analysis avoids unnecessarily reducing the model to a PlantUML
representation before analysis.

### Enable cross-model reasoning

The greatest value of the emerging toolchain lies not merely in
generating diagrams or enums, but in reasoning about the agreement
between independently useful system views.

### Make derived artefacts reproducible

C++, diagrams, signal enumerations, STTs, and consistency reports should
be regenerated from authoritative models wherever possible.

## Consequences

### Positive

-   two clear peer authorities describe complementary system concerns;
-   QM retains its code-generation advantage;
-   `.collab` remains focused on collaboration rather than behavioural
    detail;
-   per-AO PlantUML HSMs remain useful without becoming competing
    sources of truth;
-   future tooling can exploit information elsewhere in the QM
    application model;
-   model completeness and behavioural completeness fit into one
    coherent architecture;
-   shared analysis can identify inconsistencies that neither QM nor the
    collaboration model can detect alone.

### Costs and risks

-   a reliable QM model reader will eventually be required;
-   the common semantic model must preserve distinctions between the two
    authoritative sources;
-   QM format evolution may require reader maintenance;
-   hand-authored PlantUML HSMs need a clear transition of authority
    when transferred into QM;
-   cross-model diagnostics require carefully defined invariants to
    avoid false errors.

## Alternatives Considered

### Treat one `.qm` file as belonging to each AO

Rejected because it misrepresents the actual scope of the QM application
model and unnecessarily fragments behavioural authority.

### Treat per-AO `.puml` files as permanent authoritative peers

Rejected because once the same HSM exists in QM this creates competing
behavioural sources and a synchronisation problem.

### Use generated PlantUML as the mandatory intermediate model

Rejected as the long-term architecture because conversion from QM to
PlantUML can discard information useful to model analysis.

### Merge collaboration and behaviour into one new DSL

Rejected. The existing models have complementary strengths. The
objective is to reconcile authoritative views, not invent another
monolithic representation.

## Implementation Direction

Proceed incrementally:

1.  maintain `system.collab` as the complete
    collaboration/system-participant model;
2.  maintain one application-level `system.qm` containing the AO
    behavioural models;
3.  keep the reference architecture diagram at
    `doc/diagrams/model-toolchain.puml`;
4.  implement or refine `qm2puml` to extract individual AO HSM views;
5.  factor `.collab` parsing so it can feed shared analysis;
6.  investigate the structure and useful content of QM XML before fixing
    the QM reader interface;
7.  develop a common semantic representation sufficient for signal
    integration and completeness checking;
8.  move unified enum generation onto that integrated model;
9.  develop STT generation/checking against the same model;
10. add explicit cross-model consistency checks as invariants become
    well understood.

## Emerging Principle

> **The application is described by complementary authoritative models,
> not by one file that must contain every concern.**

For this toolchain:

> **`system.collab` says who participates and who communicates with
> whom. `system.qm` says how the application behaves. Tooling reconciles
> these peer models to generate implementation artefacts, documentation,
> and evidence of model completeness.**

The purpose of the surrounding tooling is therefore not merely code
generation.

It is to increase confidence that the collection of executable state
machines constitutes a complete and mutually consistent system design.
