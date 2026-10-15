# ADR-0011: Establish the Domain Information Model as an Essential Architectural Artefact

- **Status:** Proposed
- **Date:** 2026-10-15
- **Project:** `collab`
- **Related:** ADR-0010 — Intellectual Foundations and Collaboration Validation Principles

## Context

Experienced analysts and engineers strive to explain a system coherently **before developing detailed state-machine behaviour**.

A Domain Information Model (DIM) provides an essential part of that explanation. It identifies the classes within a domain, their relationships, multiplicities, responsibilities and constraints.

Although QM captures classes and their behavioural implementations, it does not provide a complete representation of the relationships that characterise a DIM.

Consequently, important architectural knowledge may remain implicit in code, dispersed through state machines, or absent from the documented model.

A collaboration diagram complements the DIM by identifying how participating objects communicate, but cannot replace its structural description.

## Decision

**Recognise the Domain Information Model as an essential, first-class architectural artefact, complementary to the collaboration model and individual state-machine models.**

The DIM should establish, in natural language wherever appropriate:

- The principal domain classes and their responsibilities.
- The associations between classes, including multiplicities.
- The structural constraints and relationships that characterise the domain.

The DIM and collaboration model should be developed together, before detailed state-machine design.

They establish the architectural context within which individual state machines are subsequently constructed.

Behavioural modelling may reveal deficiencies in the architecture, prompting deliberate refinement of the DIM and collaboration model.

## Consequences

The intended modelling approach comprises three complementary descriptions:

1. **Domain Information Model:** What objects exist, how they are related, and what responsibilities they have.
2. **Collaboration Model:** How those objects communicate to fulfil their responsibilities.
3. **State-Machine Models:** How individual objects behave.

These descriptions should be mutually consistent.

A future textual DSL for Domain Information Models may provide a means of capturing structural relationships and responsibilities alongside `collab`, potentially sharing class definitions and enabling additional validation.

This ADR establishes the architectural requirement, **not a commitment to develop that DSL or a decision about its syntax or implementation**.

## References

Mellor, Stephen J., and Marc J. Balcer. *Executable UML: A Foundation for Model-Driven Architecture*. Addison-Wesley, 2002.

ADR-0010 — Intellectual Foundations and Collaboration Validation Principles.
