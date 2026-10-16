# ADR-0016: Logical Collaborations and Application Signal Classification

- **Status:** Proposed
- **Date:** 2026-10-16
- **Project:** collab
- **Related:** ADR-0015; DPP model inspection Report 001

## Context

The DPP investigation identified a human operator who initiates PAUSE and SERVE through a physical button. The BSP's polling, debounce and QP event publication implement that interaction but do not constitute separate conceptual collaborators. In the rain-gauge design, a reed switch is similarly an external source of a switch-closing occurrence regardless of whether an ISR, processor wake-up or polling detects it.

The BucketSensor HSM also uses synchronous GPIO observations, conditional self-posts (such as SWITCH_CLOSED or SWITCH_OPEN) and CONTINUE to make transitory activity explicit. These are meaningful HSM behaviours but do not warrant extending the collaboration diagram to synchronous information exchange.

The current generator creates a QP-compatible signal enum from collaboration declarations only. It cannot yet include internal HSM signals or distinguish published from directly posted signals for QP publish-subscribe configuration.

## Decisions

1. **Keep collaboration diagrams strictly about asynchronous logical signals.** They describe communication among active objects and external entities, not synchronous observations, GPIO reads, physical interface circuitry, or implementation control flow.
2. **Introduce `external <Name>` as the preferred declaration for an entity outside the active-object system.** Render it as a labelled UML actor (stick figure) in PlantUML. Examples include `User` in DPP and `BucketReedSwitch` in the rain gauge.
3. **Treat BSPs, ISRs, polling loops, button circuitry and RC filters as implementation mechanisms**, not collaborators solely because they detect or deliver a signal. An external signal denotes a logical occurrence, not a claim that hardware constructs a QP event. Validator evidence may inspect these mechanisms and QSpy traces, with explicit provenance and mapping assumptions.
4. **Keep HSM-internal behaviour out of the collaboration diagram.** Synchronous GPIO observations belong in HSM actions; self-posted observation events and CONTINUE belong in HSM behaviour. This ADR does not settle whether every self-post should be represented as a collaboration; for the present scope, internal self-posts are excluded.
5. **Aim for a unified application signal catalogue** derived from the collaboration contract plus an HSM/internal signal inventory. Classify signal identities as *collaborative* or *implementation/internal* according to their role in the model. Independently classify the delivery mechanism as *published*, *directly posted* or *unresolved*. Do not equate collaborative with published or internal with posted.
6. **Generate a candidate QP/C++ signal header** from that unified catalogue, with the correct application-signal start, publish-subscribe sentinel/boundary and final signal sentinel for the selected QP version. Exact marker placement, names, ordering and signal-inventory input remain design and verification work, not fixed syntax in this ADR.

## Examples and boundaries

A DPP collaboration may declare `external User` and logical `User -> Table` signals PAUSE and SERVE. The validator must not demand a QM class called User or infer that the human directly calls `PUBLISH`.

A rain-gauge collaboration may declare `external BucketReedSwitch` and `BucketReedSwitch -> BucketSensor` signal BUCKET_SWITCH_CLOSING, followed by `BucketSensor -> Control` signals BUCKET_TIPPED and BUCKET_TIP_REJECTED. BucketSensor's debounce/qualification logic, GPIO reads, self-posts and CONTINUE are HSM concerns. Whether every physical closure is detected or accepted is a separate behavioural/evidence question, not implied by the arrow alone.

## Consequences and follow-up

- Extend the parser and PlantUML generator for `external`, with focused tests and a DPP example. Retain existing `isr` support temporarily pending an inventory and compatibility decision; do not silently reinterpret it.
- Update the QM validator to avoid treating external actors as missing QM active-object classes. A conceptual external-to-AO route may need BSP/source or runtime evidence to establish its implementation.
- Keep the external-participant language change separate from the broader signal-catalogue/generator experiment.
- Locate and preserve the original BucketSensor HSM before relying on it as an authoritative model; its current repository presence has not been established.
- Revisit ADR-0015's broader boundary discussion in light of this narrower conceptual/implementation separation. ADR-0015 remains a record of the evidence and initial proposal.
