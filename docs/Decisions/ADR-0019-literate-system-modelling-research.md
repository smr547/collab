# ADR-0019: Literate System Modelling — Research Directions

- **Status:** Discussion / exploratory (no decision)
- **Date:** 2026-10-22
- **Project:** collab
- **Related:** ADR-0011, ADR-0012, ADR-0018

## Historical context

Mellor and Balcer's Executable UML offered a powerful framework of Domain Information Models (DIMs), collaborations, state machines and executable action semantics. From the author's perspective around 2005, it remained immature: the executable semantics were insufficiently defined and the Mealy/Moore state-machine approach insufficiently expressive for complex systems. Miro Samek's QP/QM tooling later demonstrated practical, concrete event-driven implementations using hierarchical state machines and rich actions. QP/QM does not itself provide explicit DIM or collaboration modelling facilities. We now have an opportunity to revisit those structural and descriptive ideas using working QP/QM implementations and AI-assisted natural-language modelling. This is a research perspective, not a claim that QP/QM implements Executable UML in full.

## Questions for further research

- **Aspects and scalability:** Can independently declared, naturally described aspects generate digestible subdiagrams from a complete collaboration model?
- **Signal filtering:** Can aspects select signals individually when the same collaborating pair participates in orthogonal concerns?
- **Literate modelling:** Can rich natural-language descriptions become first-class model content and contribute to human-readable outputs?
- **DIMs:** How should domain nouns, attributes, associations, multiplicities and verb clauses be represented?
- **Classes, instances and roles:** What exactly does a Collab participant denote, especially when multiple instances of a class exist?
- **DIM–Collab–QM integration:** How can DIM entities, collaboration participants and QM AO/timer classes share identities without duplicating definitions?
- **Mechanisms and externals:** How should physical mechanisms and external entities without natural QM class representations appear in the DIM?
- **Use cases and sequence diagrams:** Can collaboration participants and signals support scenario-specific sequence diagrams, and what additional ordering semantics are necessary?
- **Traceability:** Can natural-language intent be followed through DIMs, collaborations, scenarios, HSMs and C/C++ implementation?
- **Executable arguments:** How might models, tests and QS/QSpy traces supply bounded, inspectable evidence about implementation behaviour?
- **AI-assisted modelling:** Can AI recover models, propose descriptions and identify inconsistencies, with deterministic verification of checkable claims?
- **Modelling architecture:** Should DIMs, collaborations, aspects and scenarios remain separate interconnected artefacts instead of expanding one language indefinitely?

## Important distinctions

A DIM association is not necessarily a communication relationship. A collaboration describes possible interactions, not an execution order. An aspect is a potentially overlapping projection of those interactions. A sequence diagram describes a scenario, not necessarily a unique ordering in a concurrent system. Natural language communicates intent; formal models constrain interpretation; running systems and traces provide limited observational evidence.

## Suggested first experiment

Develop a Fly 'n' Shoot DIM using the existing QM and Collab models as evidence, while identifying domain facts that require designer judgement. Focus especially on the distinction between **classes, instances and roles**, and on associations, multiplicities and verb clauses.

## Overarching research question

> Can the structural and descriptive disciplines of Executable UML, QP/QM's concrete behavioural implementation and AI's natural-language capabilities be combined to make literate, traceable and experimentally verifiable system modelling practical?

## Outcome

**No architectural decisions are made.** This ADR preserves a research agenda for future investigation. It does not approve language, compiler, tooling or implementation changes.
