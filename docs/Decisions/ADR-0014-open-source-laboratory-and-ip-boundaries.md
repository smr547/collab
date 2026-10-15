# ADR-0014: Open-Source Laboratory and Intellectual-Property Boundaries

- **Status:** Proposed
- **Date:** 2026-10-16
- **Project:** collab
- **Related:** ADR-0010, ADR-0012, ADR-0013

## Context

Miro Samek of Quantum Leaps offered a QP/C++ Extras evaluation package for the STM32 laboratory, subject to proprietary licensing and confidentiality conditions. The conditions expressly prohibit exposing the proprietary package to AI systems.

After considering the offer, the project author decided **not to download** the proprietary evaluation software. The public/open-source QP/C++ and QM material is adequate for the current investigation into collaboration specifications and validation. The overriding practical concern is avoiding accidental disclosure during AI-assisted engineering.

Miro also suggested more substantial public examples in `qpcpp/examples/posix-win32` and educational video playlists. The project author has already studied the playlists extensively; these recommendations inform future experiments but do not change the immediate DPP test plan.

## Decision

**Keep the collab exploration and its AI-assisted workflow within materials that may lawfully be inspected, discussed and shared under their applicable licences.** Do not download or introduce the offered proprietary QP/C++ Extras package into this workflow.

Use the existing public QP/C++/QM examples and the project's own models and code for DPP validation, followed where useful by more complex public examples.

Maintain a clear boundary between public reference implementations, our independently authored specifications, and third-party intellectual property. Respect all applicable open-source licence terms and attribution requirements; public availability does not mean unrestricted reuse.

## Rationale

The proprietary package is not necessary for the current architectural questions. Declining it avoids an avoidable risk of exposing restricted code to AI tools, repositories, indexing or publication.

This is a project-specific decision about scope and workflow, **not** a judgement on the value of QP Extras, QS tracing, commercial licensing or Miro's generous offer.

The correspondence has opened a constructive technical exchange. A future communication could share independently developed findings after the DPP validation experiment produces concrete results; no such outreach is required by this ADR.

## Consequences

- No proprietary Extras source, binaries or licensed excerpts should be uploaded to the project repository or supplied to AI tools.
- Current work proceeds without the evaluation-only QS/QSPY features. If tracing becomes necessary, reconsider the options and applicable terms explicitly rather than silently crossing this boundary.
- Keep Miro's public DPP QM example unchanged as a reference/negative validation specimen.
- The project remains positioned to publish its own architectural specifications, tools and findings, subject to normal licensing and attribution review.

## References

- Quantum Leaps correspondence dated 14–15 October 2026 (private correspondence; not reproduced or attached).
- Public QP/C++ examples and applicable licences.
- Engineering discussion, 15–16 October 2026.

**Status remains Proposed pending review.**
