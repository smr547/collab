# ADR-0013: Repository as Authoritative Engineering Memory

- **Status:** Proposed
- **Date:** 2026-10-16
- **Project:** collab
- **Related:** ADR-0010, ADR-0011, ADR-0012

## Context

Extended human–AI engineering discussions have exposed a practical weakness: AI conversational memory can recover a broad narrative without reliably preserving the exact decisions, qualifications, rejected alternatives and unresolved questions. A plausible reconstruction is not an adequate substitute for the actual engineering record.

The project has already developed a productive countermeasure: record significant conclusions and their rationale in Architecture Decision Records (ADRs), commit them to GitHub, and inspect the repository when resuming work. DIMs, collaboration specifications and behavioural models provide additional durable evidence.

This practice has made it possible to resume an investigation with greater precision and fidelity than conversational recall alone.

## Decision

**Treat the version-controlled repository as the authoritative engineering memory for collab.** Conversation is the medium for exploration, challenge, synthesis and discovery; reviewed and committed artifacts are the durable record of agreed architectural knowledge.

In particular:

1. Record significant architectural decisions in ADRs, including context, decision, rationale, consequences, references and explicitly deferred questions.
2. Preserve domain semantics in DIMs, communication contracts in collaboration models, and detailed behaviour in state-machine models; do not expect ADRs to replace those artifacts.
3. On resuming work, inspect the relevant repository state and ADRs rather than assuming conversational recollection is accurate.
4. Distinguish a proposal, a draft awaiting review, and an accepted decision. A PR is an invitation to review, **not** approval. Do not silently promote a proposal into an accepted fact.
5. If new evidence contradicts an earlier decision, reconcile it explicitly, recording the supersession or revision and the reasons.
6. Identify the branch or revision being examined when this matters; local uncommitted work may differ from the remote repository.

## Rationale

A model or ADR is a portable, reviewable statement of shared understanding. It can be read by a human engineer, a different AI session or a future collaborator without reproducing the entire conversation.

The distinction between **what** was decided and **why** it was decided is critical. Without the rationale, later changes risk repeating previously rejected designs or misinterpreting intentional constraints.

This process is also a way to manage AI fallibility: confidence and fluent prose must not substitute for source-grounded inspection.

## Consequences

- The repository becomes a durable interface between engineering sessions, not merely a code store.
- Important discoveries should be distilled into artifacts before they disappear into conversation history.
- ADRs remain concise and decision-oriented; not every exploratory remark requires an ADR.
- The approach improves reproducibility and onboarding but does not eliminate the need for human review, source verification or testing.
- A new session may begin by reading relevant models and ADRs, establishing an explicit common starting point.

## Broader observation, not a technical requirement

Our exploration suggests that AI's engineering value may lie less in typing code quickly than in sustained reasoning across abstraction levels. The World Wide Web made knowledge easier to access and distribute; AI may make it easier to work with that knowledge. This is an observation motivating the method, **not** a claim that the method has been quantitatively validated or that productivity gains are automatic.

## References

- ADR-0010 through ADR-0012.
- Engineering discussion, 15–16 October 2026.

**Status remains Proposed pending review.**
