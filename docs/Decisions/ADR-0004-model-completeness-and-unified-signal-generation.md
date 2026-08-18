# ADR-0004: Derive the Unified Application Signal Catalogue from Complete System and Behavioural Models

-   **Status:** Accepted
-   **Date:** 2026-08-18
-   **Project:** collab / HSM model tooling
-   **Supersedes:** ADR-0002
-   **Related:** ADR-0003 --- Allow One Signal to Have Multiple Sources
    When Receiver Semantics Are Identical
-   **Related:** ADR-0005 --- Generate State Transition Tables and
    Classify Undefined State/Event Cells

## Context

ADR-0002 proposed extending the `.collab` language so that signals local
to an Active Object could be declared explicitly in the system
collaboration model. Experience modelling `BucketSensorAO` has shown
that this would duplicate information and create an avoidable
synchronisation obligation.

The collaboration model and the HSM model answer different questions:

-   the system collaboration model describes **who participates in the
    system and who can send which signals to whom**;
-   each AO HSM describes **how that AO behaves and which signals its
    behaviour actually uses**.

For example, `BUCKET_SWITCH_CLOSING` is an inter-participant signal and
belongs in the collaboration model. Signals such as `SWITCH_OPEN`,
`SWITCH_CLOSED`, and `TIMEOUT` can instead be local behavioural stimuli
of `BucketSensorAO`. Their existence follows from the HSM itself.

Requiring those local signals to be copied into `.collab` would create
two sources of truth and permit the collaboration model and HSM to
diverge.

ADR-0003 also established that a signal has a semantic identity
independent of the number of routes by which it can arrive. The unified
C++ enum therefore represents application signal identities, not
collaboration-route occurrences.

These observations lead to a broader concept: **model completeness**.

If the system `.collab` file is defined to be a complete description of
the system participants and all inter-participant signal routes, it can
serve as the system manifest against which the set of behavioural models
is checked.

## Decision

ADR-0002 is superseded.

The `.collab` language shall **not** be extended merely to duplicate
AO-local signal declarations already authoritative in behavioural
models.

Instead, the application signal catalogue shall be derived by an
integration tool from:

1.  one complete system `.collab` model; and
2.  the behavioural HSM models for the system AOs.

Conceptually:

``` text
rain-gauge.collab
        +
BucketSensorAO.puml
ControlAO.puml
RadioAO.puml
        |
        v
shared model analysis
        |
        +--> completeness diagnostics
        +--> cross-model signal diagnostics
        +--> unified application signal catalogue
        +--> generated AppSignals enum
```

The generated enum is a **derived artefact**. No human-maintained file
shall duplicate the complete application signal list.

## Authority of the Models

### System collaboration model

The `.collab` file is authoritative for:

-   the complete set of system participants;
-   participant kinds;
-   inter-participant collaborations;
-   inter-participant signal routes;
-   semantic identities of signals carried on those routes.

The system model is therefore also a manifest of the behavioural
artefacts expected for behavioural participants.

### Behavioural HSM models

Each AO HSM is authoritative for:

-   states and hierarchy;
-   transitions;
-   event triggers used by that behaviour;
-   entry, exit, and transition actions represented by the modelling
    notation;
-   signals used only within that AO.

PlantUML HSMs are the initial textual behavioural input. QM remains the
intended authoritative executable HSM representation for production
models. The tooling architecture should permit a future QM reader
without changing the overall integration design.

### Derived application signal catalogue

The unified application signal catalogue is the union and reconciliation
of signal identities discovered in the system and behavioural models. It
is not independently maintained.

## Participant Kinds

The Rain Gauge model exposed `BucketReedSwitchISR` as a participant that
is a signal source but is not an Active Object. The existing warning
that its name does not end in `AO` is evidence that the DSL currently
conflates participant kinds.

The collaboration language should evolve to distinguish at least:

``` text
ao  BucketSensorAO
ao  ControlAO
ao  RadioAO
isr BucketReedSwitchISR
```

Further participant kinds should be added only when concrete modelling
experience justifies them.

Participant kind matters to completeness checking. An `ao` normally
requires an HSM model; an `isr` does not.

## Model Completeness

A complete system model allows tooling to determine whether required
behavioural artefacts are missing.

If `rain-gauge.collab` declares:

``` text
ao BucketSensorAO
ao ControlAO
ao RadioAO
isr BucketReedSwitchISR
```

but only `BucketSensorAO.puml` and `RadioAO.puml` are supplied, the tool
can diagnose:

``` text
ERROR: missing HSM model for AO ControlAO
```

It must not require an HSM for `BucketReedSwitchISR`.

A complete model set therefore means, at minimum:

-   every participant required to have behaviour has a corresponding HSM
    model;
-   every inter-participant signal route is represented by the system
    collaboration model;
-   signal identities used by HSMs can be reconciled with the complete
    system model;
-   the unified signal catalogue can be generated without duplicated
    declarations.

This is the first use of **model completeness** in this toolchain. It is
expected to grow beyond artefact presence into semantic consistency
checking.

## Signal Classification by Reconciliation

Once the system collaboration model is known to be complete, the
integration tool can classify HSM signal usage.

### Routed signals

A signal present in `.collab` is an inter-participant signal. Its route
or routes are explicitly defined by the system model.

For example:

``` text
BUCKET_SWITCH_CLOSING

BucketReedSwitchISR -> BucketSensorAO
ControlAO           -> BucketSensorAO
```

ADR-0003 applies: this is one semantic signal identity with multiple
valid routes.

### AO-local signals

A signal used by an AO HSM but absent from the complete system
collaboration model is local to the behavioural model, subject to the
semantics of the HSM notation.

Examples may include:

``` text
SWITCH_OPEN
SWITCH_CLOSED
TIMEOUT
```

These need not be repeated in `.collab`.

This inference is valid because the `.collab` model is assumed complete.
Without that completeness guarantee, absence from `.collab` would not
establish locality.

## Cross-Model Consistency Checking

The integration tool should evolve beyond enum generation into a model
checker.

Useful checks include:

-   an AO declared in `.collab` has no HSM artefact;
-   a routed signal delivered to an AO is not handled anywhere in that
    AO's HSM;
-   an HSM appears to consume an external signal for which the complete
    collaboration model contains no route;
-   a signal name is reused inconsistently;
-   a behavioural artefact exists for a participant not declared in the
    complete system model;
-   duplicate or contradictory model declarations exist.

Diagnostics should distinguish errors from warnings where semantic
certainty is limited.

The first implementation should prefer checks based on structurally
recognisable HSM information, especially transition triggers. It should
not attempt to infer arbitrary signal production by parsing unrestricted
C++ action text.

## Unified Enum Generation

Generation of `AppSignals` shall be separated conceptually from
`collabc`.

`collabc` remains responsible for parsing, validating, and rendering the
collaboration model.

A separate signal integration/generation tool shall consume the
collaboration model and HSM models, build a unified signal model, and
generate the C++ enum.

A possible command shape is:

``` bash
signalgen rain-gauge.collab     BucketSensorAO.puml     ControlAO.puml     RadioAO.puml
```

producing:

``` text
rain-gauge-signals.hpp
```

The exact command name and interface are not fixed by this ADR.

The generator shall preserve stable, deterministic ordering so generated
C++ does not change gratuitously between builds.

## Shared Internal Model

The collaboration compiler, signal generator, STT tooling, and future QM
integration should share parsers and an internal semantic model rather
than independently rediscovering the same information.

``` text
.collab reader -----+
                    |
.puml HSM reader ---+--> common model --> analyses/generators
                    |
.qm HSM reader -----+        (future)
```

This is an architectural direction, not a requirement to build a large
framework before the immediate tools are useful.

## Rationale

### Single source of truth

Information should be declared where it naturally becomes authoritative.

Inter-participant routing belongs in the collaboration model. Local
behavioural signal usage belongs in the HSM. The complete application
vocabulary is derived.

### Eliminate synchronisation errors

Removing AO-local declarations from `.collab` avoids updating two files
whenever an HSM adds, renames, or removes a local signal.

### Turn code generation into model analysis

Once the generator reconciles multiple authoritative models, it can
detect missing artefacts and inconsistent signal usage. The tool becomes
a software-engineering checker rather than merely a text generator.

### Preserve compatibility with QM

PlantUML is useful as a textual design and analysis format, but QM
remains valuable because it code-generates the executable C++ HSM.
Behavioural-model parsing should therefore be replaceable. A future QM
reader can provide the same semantic information directly from the
executable model source.

## Consequences

### Positive

-   no duplicated AO-local signal catalogue;
-   unified enum is derived from authoritative models;
-   missing HSM artefacts become detectable;
-   routed versus local signals can be inferred;
-   ADR-0003 multi-route signal semantics fit naturally;
-   cross-model consistency checking becomes possible;
-   the architecture creates a bridge between system collaboration
    modelling and QM;
-   future analysis tools can share the same semantic model.

### Costs and risks

-   HSM parsing becomes part of the toolchain;
-   PlantUML is descriptive rather than a formally constrained
    executable language, so parsing must initially target a disciplined
    house style;
-   participant kinds must be represented in `.collab`;
-   diagnostics must avoid claiming semantic certainty where only
    textual inference is possible;
-   the toolchain will require careful versioning as PlantUML and QM
    readers evolve.

## Alternatives Considered

### Retain ADR-0002 `internal-signals` declarations

Rejected because it duplicates information already authoritative in the
HSM and creates a synchronisation burden.

### Keep enum generation entirely inside `collabc`

Rejected as the long-term design because `collabc` alone cannot see
HSM-local signals and should not require those signals to be copied into
the collaboration model.

### Maintain the C++ enum manually

Rejected because it creates another source of truth and forfeits
consistency checking.

### Generate an enum independently from each HSM

Rejected because application signal identity spans the whole system and
includes inter-participant routes. A unified system-level catalogue is
required.

## Implementation Direction

Proceed incrementally:

1.  add explicit participant kinds needed by real models, beginning with
    `ao` and `isr`;
2.  factor collaboration parsing/model data so other tools can reuse it;
3.  define a disciplined PlantUML HSM convention sufficient to extract
    states and transition triggers;
4.  implement discovery/checking of required AO HSM artefacts;
5.  reconcile collaboration and HSM signal identities;
6.  generate one deterministic unified `AppSignals` enum;
7.  add cross-model diagnostics as their semantics become well-defined;
8.  later add a QM reader so production QM models can become the direct
    behavioural authority.

## Emerging Principle

> **Declare information in the model that is naturally authoritative for
> it; derive system-wide views from those authoritative models rather
> than maintaining duplicated declarations.**

For this toolchain:

> **The complete collaboration model defines the system and its
> inter-participant signal routes. Each HSM defines its behaviour and
> local signal usage. Model-analysis tooling reconciles them, checks
> completeness, and derives the unified application signal catalogue.**

## Status of ADR-0002

ADR-0002 is superseded by this decision.

Its motivating requirement remains valid: the generated application enum
must include AO-local signals. What changes is the mechanism. Local
signals are no longer declared redundantly in `.collab`; they are
discovered from the authoritative behavioural models.
