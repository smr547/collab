# ADR-0017: Preserve Domain Vocabulary Across Models and Code

- **Status:** Proposed
- **Date:** 2026-10-17
- **Project:** collab (principle also applicable to DIMs)
- **Related:** ADR-0015, ADR-0016; DPP model inspection Report 001

## Context

The DPP collaboration experiment exposed a vocabulary mismatch between a readable domain model and the historical QP/C++ example. In the collaboration, `DONE_EATING`, `PAUSE_SERVING` and `RESUME_SERVING` express the intended occurrences more precisely than `DONE`, `PAUSE` and `SERVE`. Likewise, the QM implementation class `Philo` abbreviates the model participant `Philosopher`.

Mappings can reconcile these names for historical inspection, but using them routinely would allow models and implementation to develop separate dialects. That undermines the purpose of literate, executable models. By contrast, systematic programming conventions such as the QP `_SIG` suffix or an `m_` instance-member prefix carry technical information without changing a domain identifier.

## Decision (proposed)

**Use one precise domain vocabulary across DIMs, collaboration models and implementation code.** Model names are architectural identifiers, not merely diagram labels.

1. **Preserve domain nouns and verbs faithfully.** Active-object names, domain attributes, events and signals should retain their meaningful identifiers across models, generated declarations and hand-written code. Do not abbreviate or substitute synonyms merely for coding convenience.
2. **Prefer literate, unambiguous event names.** For the new DPP model and implementation, prefer `DONE_EATING`, `PAUSE_SERVING` and `RESUME_SERVING` over `DONE`, `PAUSE` and `SERVE`. Retain short names such as `EAT` or `HUNGRY` where their meaning is already clear in context.
3. **Treat systematic coding decorations as conventions, not domain aliases.** For example, `DONE_EATING` in a model may become `DONE_EATING_SIG` in QP/C++; an attribute may acquire a conventional `m_` prefix. Tools may recognize documented, deterministic conventions without requiring an arbitrary name map.
4. **Permit explicit name mappings for legacy or external integration, but discourage routine use.** Mappings must be deliberate, reviewable and visible in validation reports. A mapping establishes an asserted correspondence for inspection; it does not by itself prove semantic equivalence.
5. **Generate faithful names by default.** Code generators must not silently shorten or rename domain identifiers. Validation should prefer exact matches after documented coding conventions and identify any remaining vocabulary divergence.
6. **Keep terminology and behavioural correctness separate.** Matching names does not prove that two implementations have the same event semantics, reachability or handling behaviour.

## DPP application

The historical DPP example remains valuable as independent evidence and need not be renamed in place. Its `Philo`, `DONE_SIG`, `PAUSE_SIG` and `SERVE_SIG` identifiers may require explicit, justified mappings during comparison.

A future `collaborative_dpp.qm` is intended to use the DIM and collaboration vocabulary directly, including `Philosopher`, `DONE_EATING_SIG`, `PAUSE_SERVING_SIG` and `RESUME_SERVING_SIG`, subject to the model being revised and agreed. This ADR records naming intent, not a claim that those changes have been implemented.

Proposed removal of apparently redundant HSM transitions is **out of scope**. In particular, distinguishing an event that cannot occur from one intentionally ignored or unexpectedly received requires a separate examination of contracts, event handling and defensive programming before transitions are deleted.

## Consequences

- New DIMs, Collabs and implementations should share a domain glossary and preserve its spelling.
- The existing QM identity mapping facility remains available for historical comparison; tooling may later report mapping use and naming divergence explicitly.
- The current DPP example and compiler are not changed by this ADR.
- Future work may separately specify systematic naming conventions and validation diagnostics; no new mapping grammar is approved here.
