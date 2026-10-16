# DPP model inspection — Report 001

**Status:** Experimental — provenance established; model analysis pending.

## Inputs

- **QM behavioural model:** Quantum Leaps QP/C++ 7.3.2 archive, `qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm`. Source and byte-comparison procedure are documented in [README.md](README.md).
- **Collaboration contract:** independently authored `examples/DPP.collab`; exact source revision pending commit/confirmation.

## Method

Compare only the `.collab` and `.qm` source models in the first inspection pass. Do not use generated C++ to settle ambiguous findings at this stage. Classify findings as **satisfied**, **missing**, **unexpected**, or **undetermined** and identify evidence and interpretation separately.

## Findings

_No cross-model findings have been established yet. In particular, earlier discussion of possible `DONE_SIG` handler discrepancies remains a hypothesis to investigate, not a validated defect._

## Next steps

1. Commit/identify the exact `DPP.collab` input.
2. Inspect the verified QM source and capture specific state/handler/action evidence.
3. Produce a structured inspection matrix before implementing the executable validator.
