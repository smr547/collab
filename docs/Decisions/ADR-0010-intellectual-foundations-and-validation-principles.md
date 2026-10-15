# ADR-0010: Intellectual Foundations and Collaboration Validation Principles

- **Status:** Proposed
- **Date:** 2026-10-15
- **Project:** collab
- **Related:** ADR-0001, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0009

## Context

The design of `collab` draws on Stephen J. Mellor and Marc J. Balcer's *Executable UML: A Foundation for Model-Driven Architecture* (Addison-Wesley, 2002). These ideas influenced the project's author during Executable UML studies in 2006.

What began as a textual language for collaboration diagrams is developing into a specification and validation tool for communicating state machines. QP/C++ and QM examples—especially Dining Philosophers (DPP) and Fly 'n' Shoot—provide concrete tests of the approach.

This ADR records the intellectual foundations, our proposed extensions, and the intended validation principles. It does not settle DSL grammar or graphical notation.

## 1. Models are distinct from diagrams

**Foundation.** Mellor and Balcer distinguish the underlying model from its representations. A statechart and a state transition table may represent the same behaviour and must be consistent. Modelling tools may prevent inconsistencies, audit for them, or derive one representation from another.

**Application.** Distinguish the semantic collaboration model, its textual DSL representation, its graphical collaboration diagram, and the corresponding QM behavioural models. The diagram is a deliberately selective view, not the whole semantic model (ADR-0008 and ADR-0009).

## 2. Collaboration analysis precedes detailed state machines

**Foundation.** Mellor and Balcer describe experienced modellers sketching collaborations before constructing state machines, then evaluating the resulting domain dynamics against the implemented models. Executable UML collaboration diagrams show the overall signal communication structure rather than a single execution scenario (section 10.3, pp. 178–180).

**Our design principle.** **A collaboration diagram should be developed before the individual state machines.** The thinking needed to establish collaborations is instrumental to identifying objects and external actors, defining their boundaries, partitioning responsibilities, and discovering their required signals.

This analysis is also a strong input to the **Domain Information Model** (class diagram). The roles and responsibilities of identified classes should be described in natural language before detailed state-machine semantics are considered. The Domain Information Model and collaboration model are complementary and may be refined iteratively.

The intended design and validation cycle is:

1. Identify domain objects, external actors, and their responsibilities.
2. Develop the Domain Information Model and collaboration contracts.
3. Construct the individual state machines.
4. Compare implemented communication behaviour with the independently specified collaboration contracts.
5. Resolve discrepancies deliberately, refining the appropriate model.

A future DSL for Domain Information Models is an intriguing possibility, **not a decision or implementation commitment of this ADR**.

## 3. Anonymous instances and class-level collaborations

**Foundation.** Mellor and Balcer adopt underlined UML instance notation `instanceName:ClassName`. Omitting the instance name gives an anonymous, unspecified instance, such as underlined `:Order` (section 10.3.1, p. 179).

**Application.** The diagram normally represents communication between arbitrary instances of classes, not every runtime instance. One `:Philosopher` participant can express the collaboration applicable to five Philosopher instances. Underlining does **not** imply singleton cardinality. Instance multiplicity and ownership remain separate semantic concerns.

## 4. External entities and non-AO participants

**Foundation.** External entities can send and receive signals and may be shown as actors or stereotyped boxes (section 10.3.1, pp. 179–180).

**Extension.** Event communication may involve physical external entities, ISRs, device drivers, passive HSMs, timers, and startup sources, as well as Active Objects. Participation is not determined solely by inheritance from `QActive`. Distinguish a physical event source, the software mechanism that injects an event, and the receiver; the primary diagram need not display all intermediate machinery.

## 5. First-class timers

**Foundation.** Mellor and Balcer conventionally omit signals generated and received within the same state machine, leaving those details to the state machine itself (section 10.3.1, p. 180).

**Extension.** Timers may nevertheless be architecturally significant event sources in embedded systems. DPP has a time event associated with each Philosopher instance, delivering `TIMEOUT_SIG` to that Philosopher. Fly 'n' Shoot illustrates a system-level timer publishing `TICK` to subscribers. A common Timer participant concept should accommodate both patterns, including differences in ownership, multiplicity, and delivery. A smaller timer glyph may help readability. Lifecycle details such as arming and disarming belong principally in QM. Syntax and notation are deferred.

## 6. Event identity and delivery semantics

QP supports several event-injection mechanisms, including **direct posting (LIFO or FIFO queue insertion)**, Publish/Subscribe, and synchronous dispatch. These mechanisms are not interchangeable.

The semantic model must distinguish signal identity, source, permitted receiver relationships, injection mechanism, and actual delivery. Publish/Subscribe delivers according to subscriptions; a publisher does not directly address a single receiver. ADR-0007's route-level rules and ADR-0008's more detailed separation of Signal, Route, Generation, Injection, and Delivery require reconciliation. No event-bus diagram or particular arrow syntax is mandated here.

## 7. Necessary and sufficient communication contracts

**Proposed validation objective.** Within a precisely defined scope, the collaboration specification is intended to be **necessary and sufficient** for the application's permitted and required communication contracts:

- **Completeness:** every required collaboration contract is implemented.
- **Exclusivity:** every implemented application communication contract is justified by the collaboration specification.

The comparison is bidirectional, but it is **not** a naive one-to-one comparison of routes and state transitions: an event may be legitimately delivered without triggering a transition, and one route may be handled differently in different states.

A QM handler for an application signal that is not permitted to reach its AO by any declared collaboration is a validation error, not automatically legitimate defensive coding. Validation must account for inherited handlers in superstates as well as handlers in substates.

The scope and treatment of framework signals, local/reflexive signals, runtime subscription changes, and behaviour implemented outside QM require explicit rules. Diagnostics must distinguish an incorrect implementation, an incomplete collaboration specification, and a mistaken validator interpretation.

## 8. DPP as a negative validation test

The intended DPP collaborations include:

| Source | Destination | Signal |
| --- | --- | --- |
| Philosopher | Table | `HUNGRY_SIG` |
| Philosopher | Table | `DONE_SIG` |
| Table | Philosopher | `EAT_SIG` |
| Philosopher timer | Philosopher | `TIMEOUT_SIG` |

Delivery mechanisms are part of the semantic contracts, not merely decorative annotations.

In the examined QP/C++ NUCLEO-L152RE DPP example, the Table subscribes to `DONE_SIG` and Philosopher subscribes to `EAT_SIG`, but the Philosopher HSM explicitly handles `DONE_SIG` in several states. Under the collaboration specification above, `DONE_SIG` is not an incoming signal permitted for Philosopher. These handlers are candidate validation errors.

Their educational or defensive purpose is not established; the model should be evaluated without presuming Miro Samek's intent. Moving such handlers into a common superstate might reduce repetition but would not remove the architectural inconsistency.

DPP should remain an unmodified reference specimen while the validator is developed.

## 9. Model authority and reconciliation

The independently specified collaboration model is authoritative for the communication architecture it declares. QM is authoritative for the detailed behaviour of individual state machines. Neither should silently redefine the other.

On detecting a discrepancy, the engineer must decide whether the collaboration specification, QM implementation, or validation interpretation is wrong. Generating a diagram from QM is useful for comparison, but must not automatically expand the intended collaboration contract to legitimise existing code.

## Consequences

`collab` has a purpose beyond drawing diagrams: specifying communication architecture, extracting implementation facts from QM, validating both missing and extraneous contracts, and reporting precise diagnostics. A complete semantic model may support multiple deliberately selective visual representations.

The Rain Gauge, DPP, and Fly 'n' Shoot examples provide complementary test cases.

## Deferred decisions

This ADR does not prescribe: a Domain Information Model DSL; syntax for timers or external entities; graphical notation for Publish/Subscribe; ownership and cardinality grammar; treatment of dynamic subscriptions; the exact contract-matching algorithm; or how far validation can proceed from QM alone rather than generated or handwritten C++.

## References

- Mellor, Stephen J., and Marc J. Balcer. *Executable UML: A Foundation for Model-Driven Architecture*. Addison-Wesley, 2002. Section 10.3, *Visualizing Domain Dynamics*, pp. 178–180; section 10.3.1, *Collaboration Diagrams*, pp. 178–180; sidebar *Models vs. Diagrams* (page number to be confirmed). Principles above are paraphrased; no scans are redistributed.
- Quantum Leaps, QP/C++ NUCLEO-L152RE Dining Philosophers example: `dpp.qm`, `philo.cpp`, `table.cpp`.
- `collab` ADR-0001 through ADR-0009.

**Status remains Proposed pending review.**
