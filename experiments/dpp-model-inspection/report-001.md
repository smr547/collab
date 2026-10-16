# DPP model inspection — Report 001

**Status:** Experimental — provenance established; model analysis pending.

## Inputs

- **QM behavioural model:** Quantum Leaps QP/C++ 7.3.2 archive, `qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm`. Source and byte-comparison procedure are documented in [README.md](README.md).
- **Collaboration contract:** independently authored `examples/DPP.collab`; committed at `8779714` (`examples/DPP.collab`), independently authored.

## QM input fingerprint

The user supplied the verified historical `dpp.qm` directly for inspection. The uploaded XML is 17,637 bytes, with SHA-256:

`9f64c20dfac53fae16d053c33be4b810f5d999fe6bcec45a3d68a75129798c46`

Its root declares `<model version="5.3.0" links="1">`. This fingerprint identifies the uploaded inspection input; the independently reported byte comparison establishes its relationship to the QP/C++ 7.3.2 archive.

## Preliminary observations (not yet validated findings)

- The QM model declares `Philo` and `Table` active-object classes.
- `Philo` subscribes to `EAT_SIG` and `TEST_SIG`; `Table` subscribes to `DONE_SIG`, `PAUSE_SIG`, `SERVE_SIG` and `TEST_SIG`.
- `Philo` posts `HUNGRY_SIG` to `AO_Table` on entering `hungry`.
- `Philo` publishes `DONE_SIG` when exiting `eating`; `Table` publishes `EAT_SIG` when granting permission.
- `Philo` has `DONE` handlers despite not subscribing to `DONE_SIG`. These handlers assert that any received `DONE` event is for another philosopher; this is not evidence of an incorrect route. A handler's existence does not imply that an event is delivered to it.
- `TIMEOUT_SIG` is bound to `Philo::m_timeEvt`.

These are observations of the QM source. Classification against the collaboration contract is still pending.

## Method

Compare only the `.collab` and `.qm` source models in the first inspection pass. Do not use generated C++ to settle ambiguous findings at this stage. Classify findings as **satisfied**, **missing**, **unexpected**, or **undetermined** and identify evidence and interpretation separately.

## Findings

_No cross-model findings have been established yet. In particular, earlier discussion of possible `DONE_SIG` handler discrepancies remains a hypothesis to investigate, not a validated defect._

## Next steps

1. Commit/identify the exact `DPP.collab` input.
2. Inspect the verified QM source and capture specific state/handler/action evidence.
3. Produce a structured inspection matrix before implementing the executable validator.
