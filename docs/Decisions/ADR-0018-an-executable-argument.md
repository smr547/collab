# ADR-0018: An Executable Argument — Collaboration Models and Runtime Evidence

- **Status:** Discussion / exploratory (no decision)
- **Date:** 2026-10-19
- **Project:** collab
- **Related:** ADR-0008, ADR-0009, ADR-0010, ADR-0013, ADR-0015, ADR-0016, ADR-0017; DPP model inspection Report 001
- **Reference applications:** [Dining Philosophers](../../examples/DPP.collab), [Fly 'n' Shoot Linux](https://github.com/smr547/fly-n-shoot-linux)

## Purpose

Capture a developing idea, provisionally called **“An Executable Argument”**, without adopting a design, changing the collaboration language, or making a commitment about tooling.

The phrase describes a possible way to reason about architecture: a collaboration model makes claims about a system of communicating active objects; an executable implementation provides a concrete subject of investigation; runtime instrumentation offers observations against which some of those claims can be tested.

The value is not that a diagram is automatically “proved” by running a program. Rather, the model, implementation and observations are distinct artefacts that can be inspected, questioned, compared and refined.

## The proposition worth exploring

> A collaboration model can be treated as a proposition about the architecture of a system of communicating active objects, whose claims are open to examination against an executable implementation.

An individual hierarchical state machine describes the behaviour of an active object. A collaboration diagram offers a different perspective: the relationships among participants, the logical signals exchanged, and the collective architecture that may be difficult to see by inspecting HSMs independently.

Could this perspective become a useful architectural contract, rather than simply a picture? What would count as evidence for or against its claims?

## Three complementary artefacts

1. **Collaboration model — architectural proposition.** Describes intended participants, responsibilities, logical asynchronous interactions and system boundaries. It should not be confused with a transcript of one execution.
2. **Executable application — concrete realisation.** The QM-generated HSMs, QP/C++ event framework, BSP and platform code together implement behaviour. Implementation structure and static analysis reveal possible event routes, including routes not exercised in a particular run.
3. **QS/QSpy trace — observational evidence.** Instrumentation exposes selected events, publications, posts, dispatches and transitions that actually occurred during a particular execution, subject to instrumentation and filtering.

The relationship is potentially reciprocal: models can suggest experiments, while unexpected observations can challenge the model or our understanding of the implementation.

**Crucial distinction for discussion:** A collaboration model is not merely a diagram inferred from a trace. A trace is evidence to compare with the model; it does not define architectural intent.

## Evidence, inference and limits

A useful research discipline might distinguish:

- **Declared or intended communication:** expressed in the collaboration model.
- **Statically supported communication:** plausible or reachable routes established through QM, source inspection and implementation analysis, with assumptions made explicit.
- **Observed communication:** records actually captured by QS during a specified run.

These categories are not interchangeable. Seeing a route in a trace supports its occurrence in that run, but not its occurrence in all runs. Not seeing a route does **not** prove it cannot occur: the execution may not have exercised it, a QS filter may have suppressed it, or the instrumentation may not cover it. Static source patterns alone also do not establish runtime reachability or semantic correctness.

A QS record of publication, delivery, dispatch and an HSM transition may illuminate different stages of one interaction; the exact meaning and visibility of each stage deserve examination. We should avoid conflating a logical collaboration with its QP delivery mechanism or with internal HSM behaviour (see ADR-0016).

This line of inquiry is **not** a claim of formal verification or exhaustive behavioural coverage.

## Why Fly 'n' Shoot matters now

The [Fly 'n' Shoot Linux port](https://github.com/smr547/fly-n-shoot-linux) provides an independently authored, functioning reference application rather than a toy example constructed to fit the collab DSL.

As of October 2026, its original QM-generated game state machines run under QP/C++ 7.3.2 with an SDL3 display/input adaptation. An optional QS-enabled build has successfully streamed live TCP records to QSpy 7.3.1. The trace volume is high; filtering, short controlled captures and QSpy sequence output remain potential experiments, not completed findings.

Possible investigative path:

1. Inspect the game's QM-generated source, BSP, signals and active-object relationships.
2. Build a **first-class Fly 'n' Shoot collaboration model** in collab, making the provenance and assumptions of each relationship explicit.
3. Render a readable diagram that exposes architecture without reproducing every HSM transition.
4. Design controlled runtime scenarios and examine selected QS traces for corresponding event activity.
5. Record both agreements and discrepancies between intended, statically supported and observed relationships.
6. When the model is mature, consider showing its SVG in the Fly 'n' Shoot README as a visual invitation to explore collab, with links back to the model and evidence.

The proposed README teaser should not imply that runtime validation is already complete.

## Why compare with Dining Philosophers?

Dining Philosophers (DPP) offers a compact, relatively well-understood collaboration; Fly 'n' Shoot exercises a different application structure involving operator input, periodic activity and interacting game objects.

Using both as reference applications could expose accidental assumptions in the DSL or diagram generator. A notation that represents both naturally is more persuasive than one tuned to a single example. Conversely, difficulties in modelling Fly 'n' Shoot may be useful findings rather than defects to conceal.

DPP inspection has already illustrated the need to distinguish QM descriptions, BSP-originated events and QS observations, including system-boundary interactions (ADR-0015 and ADR-0016).

## Interesting questions — not decisions

- What constitutes a *testable architectural claim* in a collaboration model? Are participants, signal identities, allowed routes, delivery semantics and boundaries equally testable?
- What is the smallest useful correspondence between a logical collaboration and one or more QS records?
- How can we distinguish publish/subscribe, direct posting, queueing, dispatch and HSM transitions without burdening the collaboration diagram with implementation detail?
- What can source inspection establish that a finite execution trace cannot, and vice versa?
- How should missing, ambiguous, filtered or contradictory evidence be reported?
- Can controlled scenarios make a trace useful without turning collab into a trace visualiser?
- Would QSpy's binary capture or sequence-diagram output be useful experimental inputs? If so, what information and provenance would have to accompany them?
- Can a model reveal undocumented coupling, unanticipated event routes or divergence between design vocabulary and implementation?
- Could collaboration models eventually guide test selection, trace interpretation or architectural regression checks?
- What would a convincing *counterexample* to a collaboration claim look like?
- How might we present an “executable argument” to another engineer so they can reproduce, challenge and improve it?

## Possible intellectual contribution

A conventional demonstration says, “Here is a diagram and here is a program.” An **executable argument** might instead say:

> Here is our architectural proposition; here is the executable system to which it refers; here are the observations and source-level evidence; here are the assumptions and limits; and here is how another investigator can challenge the correspondence.

That framing may be valuable in conversations with other QP practitioners, including Miro Samek, precisely because the argument can be independently inspected. The idea remains exploratory: we have an instrumented application, not yet a completed comparison between its QS traces and a collab model.

## Outcome of this ADR

**No architectural decisions are made.** No grammar, schema, validator, QS integration, trace format, automated conformance checker or workflow is approved here. No implementation work is authorised by this document.

This ADR preserves questions, conceptual distinctions and a promising experimental direction for subsequent discussion and separately recorded decisions, if any.
