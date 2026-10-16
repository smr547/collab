# ADR-0015: External Actors and System-Boundary Interactions

- **Status:** Proposed
- **Date:** 2026-10-16
- **Project:** collab
- **Related:** ADR-0010, ADR-0012, ADR-0013, DPP model inspection Report 001

## Context

The independently authored `examples/DPP.collab` describes three AO-to-AO signals (HUNGRY, DONE, EAT) and a timer-to-AO signal (TIMEOUT). Inspection of the historical QP/C++ 7.3.2 `dpp.qm` supports all four relationships, but the QM file is not a complete account of the executable system.

The NUCLEO-L152RE QV `qv/bsp.cpp` samples button B1 on PC13 in `SysTick_Handler`, debounces it, and publishes `PAUSE_SIG` on depression and `SERVE_SIG` on release. Table subscribes to both. QSpy traces supplied during Report 001 confirm publication, queue posting, retrieval, dispatch and Table transitions `serving -> paused` and `paused -> serving`. The same BSP directly posts `TEST_SIG` from `EXTI9_5_IRQHandler` to Table; its actual trigger and runtime occurrence were not established. A QM subscription by Philosopher to TEST does not establish a BSP-to-Philosopher delivery route.

These findings establish a coverage boundary in the current DSL and QM-only validator: the system includes human-initiated and BSP-originated interactions absent from the original collaboration contract and QM behavioural model.

## Decision (proposed)

**Extend the scope of the collaboration language to support external actors and interactions crossing the active-object system boundary.** The language design must be able to distinguish:

- an external actor (such as the human operator);
- a physical action or input (such as pressing/releasing B1);
- an implementation-side producer (such as SysTick/BSP or an ISR);
- an application signal and its recipient AO.

Preserve the distinction between *causal interaction* (button press causes event production) and *QP event delivery* (BSP publishes a signal received by Table). Do not silently equate a human actor, button, ISR and AO.

This ADR **does not approve any particular keyword, grammar, arrow semantics or new participant type**. Those alternatives belong in a follow-on design experiment and require separate review before implementation. The authoritative `examples/DPP.collab` remains unchanged.

## Rationale

A collaboration diagram that claims to describe the system boundary should not lose externally initiated behaviour merely because its event producer resides outside QM. Equally, representing the operator as though they directly published `PAUSE_SIG` would misrepresent the implementation. An explicit boundary model can preserve both the intended user interaction and the software event route.

## Consequences

- Future modelling work must examine actor, hardware/input, BSP and ISR representations, including existing `ao`, `timer` and `isr` constructs.
- Future validation may need evidence from QM, BSP/source files and QSpy, with provenance and coverage limitations reported separately.
- Source-pattern support is not proof of runtime reachability; an observed QSpy route is evidence for that execution, not exhaustive verification.
- No DSL syntax or validator implementation is mandated by this proposed decision.

## Evidence and follow-up

- `experiments/dpp-model-inspection/report-001.md` (conclusion and reproducibility record)
- Official public QP/C++ 7.3.2 `examples/arm-cm/dpp_nucleo-l152re/dpp.qm` and `qv/bsp.cpp`
- User-observed QSpy PAUSE/SERVE publication, delivery and HSM transitions, documented in Report 001

**Follow-up:** Report 002 — External Actors and System Boundaries in Collaboration Models. Evaluate representation alternatives and specify an independently reviewable DSL change.
