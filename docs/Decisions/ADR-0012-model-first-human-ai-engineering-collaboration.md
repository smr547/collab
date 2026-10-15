# ADR-0012: Model-First Human–AI Engineering Collaboration

- **Status:** Proposed
- **Date:** 2026-10-16
- **Project:** collab
- **Related:** ADR-0006, ADR-0008, ADR-0009, ADR-0010, ADR-0011

## Context

The current exploration began partly as an evaluation of AI as an engineering tool. Sustained investigations of embedded concurrency, QP/C++, QM and Executable UML have suggested a more useful question than whether AI can quickly generate code: how can a human engineer and an AI reason together, precisely and productively, about a system?

The Dining Philosophers Problem (DPP) provides a small example. A concise collaboration specification identifies Table, Philosopher and PhilosopherTimer and the four required signals: HUNGRY, DONE, EAT and TIMEOUT. Natural-language comments explain the circumstances in which each signal is generated. This gives the participants in a design discussion a coherent communication architecture before any individual HSM is designed.

However, communication alone cannot explain domain terms such as *adjacent philosophers*. Those meanings must be established in a Domain Information Model (DIM).

## Decision

**Adopt a model-first approach to human–AI design discussions.** For a new system, use a DIM and an independently specified collaboration model as primary inputs to architectural reasoning **before** constructing detailed HSMs or implementation code.

These are complementary, mutually constrained descriptions, not interchangeable representations:

- **DIM:** domain classes, associations, verb clauses at both ends of relationships, multiplicities, responsibilities and invariants. It defines the vocabulary of the problem.
- **Collaboration model:** participants, permitted/required signals, communication direction and circumstances of generation. It defines the communication contract.
- **QM/HSM models:** states, transitions, guards and actions implementing the required behaviour. They must respect the domain and communication contracts.

Design is iterative: evidence from HSM construction or execution may prompt deliberate revision of the earlier models. The implementation must not silently redefine them.

## DPP thought experiment

A preliminary DPP DIM would describe Philosophers and Forks, with left-fork and right-fork relationships and appropriate multiplicities. Verb clauses at **both** association ends give precise meaning to the relationships. Together with constraints describing a circular arrangement, they permit a definition such as: two Philosophers are adjacent when they share a Fork.

That definition belongs in the DIM, not in a signal arrow. The precise relationship structure and multiplicities remain to be modelled and reviewed; this ADR does not claim a completed DPP DIM.

The DIM can express the exclusive-use constraint on a Fork. The collaboration specification expresses the Table's grant of EAT permission. Taken together, they enable precise questions: may adjacent Philosophers eat concurrently? May nonadjacent ones do so? Can simultaneous hunger cause deadlock or starvation? Does the Table preserve the invariants?

A first-cut collaboration example is:

```text
ao Table
ao Philosopher
timer PhilosopherTimer "One-shot; thinking and eating random interval"

collaboration Philosopher Table
  Philosopher -> Table
    HUNGRY  # Philosopher has finished thinking and requests permission to eat
    DONE    # Philosopher has finished eating and releases its forks
  Table -> Philosopher
    EAT     # Table grants permission to eat
end

collaboration PhilosopherTimer Philosopher
  PhilosopherTimer -> Philosopher
    TIMEOUT # The currently armed thinking or eating interval expires
end
```

The actual working draft is `examples/DPP.collab` in the author's local workspace at the time of discussion; this ADR does **not** add or assert that file is committed. The removed TableTimer was a modelling correction: the examined DPP has no Table timer.

The `#` comments are accepted by the current parser but discarded; they document intent for human review, and are not presently machine-checkable preconditions. Retaining them as structured model metadata is a possible later improvement, not an adopted requirement.

The communication specification does not by itself encode event delivery mechanisms. For DPP, the relevant implementation distinguishes targeted posting, publication/subscription, and time-event delivery (ADR-0007 and ADR-0010). A published EAT event may reach multiple Philosopher instances; receiving an event does not mean permission applies to every instance.

## Validation implications

The DPP collaboration model is to be developed independently of Miro Samek's unmodified DPP QM example. The planned validator checks **both** required communication and extraneous communication/handlers within an explicitly defined scope. The Philosopher's DONE handlers are candidate negative tests, not evidence of Miro's intention. A successful negative test must not be made to pass by copying implementation details into the contract.

We will first review the architectural meaning of the model, then build the smallest useful validator. More complex public QP examples may follow DPP.

## Consequences

- A pair of compact, human-readable models can serve as a high-fidelity interface for sustained human–AI engineering discussions.
- Reasoning starts in domain vocabulary and explicit communication responsibilities rather than premature implementation.
- Models remain useful to humans and tools independently of any particular AI session.
- Model consistency and validation are design objectives; automated proofs of domain invariants, deadlock freedom or starvation freedom are **not** claimed.
- No DIM parser, DSL grammar, or comment-preservation mechanism is mandated by this ADR.

## References

- ADR-0010: Intellectual Foundations and Collaboration Validation Principles.
- ADR-0011: Establish the Domain Information Model as an Essential Architectural Artefact.
- Mellor, Stephen J., and Marc J. Balcer, *Executable UML: A Foundation for Model-Driven Architecture* (2002), for relationships, verb clauses, collaboration analysis and the model/diagram distinction.
- Engineering discussion, 15–16 October 2026.

**Status remains Proposed pending review.**
