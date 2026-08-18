# ADR-0005: Generate State Transition Tables and Classify Undefined State/Event Cells

-   **Status:** Accepted
-   **Date:** 2026-08-18
-   **Project:** collab / HSM model tooling
-   **Related:** ADR-0004 --- Derive the Unified Application Signal
    Catalogue from Complete System and Behavioural Models

## Context

ADR-0004 introduces **model completeness**: the complete system
collaboration model and behavioural HSM models can be analysed together
to detect missing artefacts, reconcile signal usage, and derive the
unified application signal catalogue.

A second form of completeness applies inside each HSM.

A statechart naturally emphasises transitions that **are defined**. It
is less effective at drawing attention to combinations of state and
event for which no transition is shown. Those omissions may be
intentional, impossible, harmless, erroneous, or simply forgotten.

A State Transition Table (STT) provides a complementary view:

-   states form the rows;
-   events form the columns;
-   each cell represents a candidate state/event combination;
-   defined behaviour occupies corresponding cells;
-   empty cells expose combinations for which the statechart has no
    explicit handling.

For example:

  -----------------------------------------------------------------------------------------------
  State                `BUCKET_SWITCH_CLOSING`   `SWITCH_OPEN`   `SWITCH_CLOSED`   `TIMEOUT`
  -------------------- ------------------------- --------------- ----------------- --------------
  `READY`              transition                ?               ?                 ?

  `CONFIRMING_CLOSE`   ?                         transition      transition        transition

  `TIPPED`             ?                         transition      ?                 transition

  `CONFIRMING_OPEN`    ?                         transition      transition        transition
  -----------------------------------------------------------------------------------------------

Each question mark is a design question:

> What is the intended semantic disposition if this event is presented
> while the HSM is in this state?

Systematically answering that question can reveal missing transitions,
invalid assumptions, inadequate fault handling, and incompletely
understood behaviour.

## Decision

The HSM tooling shall support generation of a State Transition Table for
each supplied AO behavioural model.

The STT is a **model-analysis and completeness artefact**, not a
replacement for the HSM.

Defined state/event behaviour is derived from the authoritative HSM.

Every otherwise undefined state/event cell shall be capable of explicit
classification by the software engineer or system designer.

A model shall not be considered transition-cell complete while relevant
cells remain unclassified.

## Purpose of the STT

The statechart remains the primary behavioural representation because it
expresses topology, hierarchy, transition structure, and actions
clearly.

The STT supplies a deliberately different projection:

> **For every event relevant to this AO, what happens in every relevant
> state?**

This makes omission visible.

The STT is therefore primarily a design-review, verification, and
completeness tool.

## Initial Undefined-Cell Classifications

The initial classification vocabulary shall include at least:

### `IGNORE`

The event can legitimately occur in this state and the intended
behaviour is to take no action. This is an explicit design decision, not
an accidental absence of a transition.

### `CANNOT_HAPPEN`

The system architecture or physical model makes this state/event
combination impossible under the stated assumptions. This classification
should invite scrutiny because it encodes an assumption that may later
become false.

### `SHOULD_NOT_HAPPEN`

The event is not expected in this state, but the system cannot prove
that it is impossible. This identifies a potentially valuable diagnostic
or defensive-design point.

### `FATAL`

Receipt of this event in this state represents a violation severe enough
to invoke the application's fatal-error/assertion policy.

### `UNCLASSIFIED`

No disposition has yet been assigned. This is the default status of an
undefined cell and represents incomplete design analysis.

Additional classifications may be introduced when real models justify
them. Candidate future classifications include `DEFER` and `FAULT`, but
they are not mandated until their semantics are clear.

## Completeness Rule

For the set of states and events relevant to an AO:

> **Every state/event cell shall either contain defined HSM behaviour or
> an explicit undefined-cell classification.**

A report containing `UNCLASSIFIED` cells is incomplete.

Example:

``` text
BucketSensorAO transition-cell completeness

States:                 5
Events considered:      7
Defined behaviour:     14
IGNORE:                  8
CANNOT_HAPPEN:           6
SHOULD_NOT_HAPPEN:       4
FATAL:                   2
UNCLASSIFIED:            1

ERROR:
    state: CONFIRMING_OPEN
    event: SOME_EVENT
    disposition: UNCLASSIFIED
```

The exact report format is not fixed by this ADR.

## Event Set

The event columns for an AO should be derived from the integrated model
established by ADR-0004.

At minimum, they include:

-   inter-participant signals routed to the AO by the complete
    collaboration model;
-   local signals used as HSM triggers by the AO;
-   other signals structurally known to be relevant to the AO.

This is another reason STT tooling should share the common semantic
model rather than independently parse files and invent its own signal
catalogue.

## HSM Hierarchy

Hierarchical state machines introduce an important complication:
behaviour may be inherited from a superstate.

An apparently empty cell for a leaf state is not necessarily undefined
if the event is handled by an ancestor state.

The STT generator/checker must therefore distinguish at least:

-   handling defined directly in the state;
-   handling inherited from a superstate;
-   genuinely undefined behaviour.

The generated table may annotate inherited handling explicitly.

## Guards and Multiple Candidate Transitions

A state/event combination may have more than one candidate transition
because of guards.

The STT cell must therefore be capable of representing multiple guarded
alternatives rather than assuming one cell equals one transition.

The checker should flag incomplete guarded partitions only when it can
do so reliably. It must not pretend to prove logical exhaustiveness of
arbitrary C++ guard expressions.

## Internal and Self Transitions

Internal transitions, self transitions, and state-preserving event
handling count as defined behaviour and should be represented distinctly
where useful.

The STT is about event disposition, not merely changes of state.

## Classification Storage

Undefined-cell classifications are analysis metadata, not executable HSM
behaviour.

They should not initially be embedded into the PlantUML statechart
merely to satisfy the checker.

A sidecar artefact is preferred, conceptually:

``` text
BucketSensorAO.puml
BucketSensorAO.stt
```

The HSM remains authoritative for defined behaviour. The STT sidecar
records the engineer's explicit disposition of combinations for which
the HSM contains no handling.

The exact sidecar syntax and extension are not fixed by this ADR. It
should be human-readable, diff-friendly, deterministic, and suitable for
version control.

When QM becomes the authoritative HSM source, the same concept can
remain:

``` text
BucketSensorAO.qm
BucketSensorAO.stt
```

## Generated Versus Authored STT Content

The tool shall distinguish derived information from human
classification.

Derived from the HSM/integrated model:

-   states;
-   hierarchy;
-   relevant event columns;
-   defined transitions/handling;
-   inherited handling.

Authored by the engineer:

-   classification of genuinely undefined cells;
-   optional rationale where useful.

Regeneration must preserve authored classifications wherever their
state/event identity remains valid.

If a state or event is renamed or removed, stale classifications should
be diagnosed rather than silently discarded where practical.

## Tool Boundary

STT generation/checking is conceptually distinct from unified enum
generation.

The tools should share parsers and the common semantic model, but STT
analysis should remain independently invokable.

Possible commands are:

``` bash
sttgen BucketSensorAO.puml
sttcheck BucketSensorAO.puml BucketSensorAO.stt
```

or an equivalent integrated interface.

The names are illustrative and are not fixed by this ADR.

This separation keeps responsibilities clear:

``` text
collabc
    collaboration validation/rendering

signal generation/integration
    system/HSM reconciliation
    unified AppSignals enum

STT analysis
    state/event matrix
    undefined-cell classification
    behavioural completeness diagnostics
```

## Model Completeness and Transition-Cell Completeness

ADR-0004 and this ADR define complementary notions of completeness.

### System/model completeness

Answers questions such as:

-   are all declared behavioural participants modelled?
-   are system signal routes consistent with supplied HSMs?
-   can the unified application signal catalogue be derived?

### Transition-cell completeness

Answers:

-   for every relevant event in every relevant state of this AO, has the
    intended disposition been explicitly considered?

A project may satisfy one form while failing the other. Both are
valuable design gates.

## Rationale

### Omissions are difficult to see in diagrams

A statechart makes existing transitions visually prominent. It does not
naturally enumerate everything that is absent. The STT turns absence
into visible cells requiring attention.

### Explicit non-handling is valuable information

There is a substantial semantic difference between deliberately ignore,
architecturally impossible, unexpected, fatal, and not yet considered. A
blank diagram does not record that distinction.

### The exercise challenges assumptions

Classifying every empty cell forces the designer to test statements such
as "that event cannot happen here." This can expose races, delayed
events, queued stale events, timer interactions, ISR timing, and
incomplete fault behaviour.

### It complements executable modelling

QM's strength is the executable HSM. STT analysis adds a systematic
review projection over that model without replacing it or requiring a
second behavioural implementation.

## Consequences

### Positive

-   undefined event handling becomes visible;
-   model omissions can be discovered before implementation testing;
-   assumptions about impossible events become explicit;
-   fault and assertion policies can be reviewed systematically;
-   the STT becomes a useful design-review artefact;
-   hierarchical inherited handling can be made explicit;
-   the same analysis can later operate directly on QM models;
-   completeness can be measured and checked automatically.

### Costs and risks

-   large AOs may produce large matrices;
-   the event set must be scoped sensibly to avoid meaningless
    combinatorial noise;
-   hierarchy, guards, deferred events, and internal transitions require
    careful semantics;
-   classifications can become stale and require validation;
-   `CANNOT_HAPPEN` can create false confidence if used casually;
-   the tool must avoid pretending to formally prove arbitrary guard
    logic.

## Alternatives Considered

### Rely only on visual HSM review

Rejected because undefined state/event combinations are not
systematically visible.

### Put an explicit transition for every combination into the HSM

Rejected because it would clutter the behavioural model and obscure
meaningful behaviour with analysis-only detail.

### Treat all undefined events as ignored

Rejected because it collapses materially different design intentions and
can conceal defects.

### Generate the STT but leave blank cells blank

Rejected as insufficient. The principal value of the STT is the
classification exercise forced by the empty cells.

### Embed all classifications in PlantUML

Deferred. This may be useful later, but initially it risks contaminating
the behavioural model with analysis metadata and tying the approach
unnecessarily to PlantUML.

## Implementation Direction

Proceed experimentally with `BucketSensorAO`:

1.  parse the states and event-triggered transitions from its PlantUML
    HSM;
2.  obtain the AO's relevant event set from the ADR-0004 integrated
    model;
3.  generate an initial state/event matrix;
4.  account for hierarchical inherited handling;
5.  represent undefined cells as `UNCLASSIFIED`;
6.  define a simple human-readable sidecar format for classifications;
7.  regenerate/check while preserving classifications;
8.  report remaining `UNCLASSIFIED` cells;
9.  use the exercise to refine classification vocabulary and HSM house
    conventions;
10. later implement the same semantic analysis against QM input.

## Emerging Principle

> **A state-machine design is not fully reviewed merely because all
> intended transitions have been drawn. The designer should also account
> explicitly for every relevant event in every relevant state.**

The STT provides the systematic mechanism for asking that question.

A defined transition says what the machine does.

A classified empty cell says that the designer has deliberately
considered what the machine should do when no transition is defined.

Both are part of behavioural model completeness.
