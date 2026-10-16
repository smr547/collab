# DPP model-inspection experiment

## Purpose

Compare an independently authored `.collab` communication contract with the original Quantum Leaps Dining Philosophers QM application model. The experiment will produce (1) a human/AI-assisted inspection report and (2) an executable cross-model validator, with their findings compared. This document records the source provenance before any inspection findings are asserted.

## Reference QM model: verified provenance

| Field | Value |
| --- | --- |
| Publisher | Quantum Leaps |
| Product distribution | QP/C++ 7.3.2 |
| Distribution archive | `qpcpp_7.3.2.zip` |
| Public source | https://sourceforge.net/projects/qpc/files/QP-Cpp/7.3.2/ |
| Path inside extracted archive | `qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm` |
| Local working file | `~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm` |
| QM XML root observed in local file | `<model version="5.3.0" links="1">` |
| Local file listing | 17,637 bytes; filesystem modification time 14 September 2023 |
| Verification | User downloaded and extracted the QP/C++ 7.3.2 archive and ran `cmp ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm dpp.qm` from the extracted example directory; command completed with no differences reported |

**Interpretation:** The user's local model was confirmed byte-for-byte identical to the `dpp.qm` extracted from the QP/C++ 7.3.2 archive. The `5.3.0` attribute is a QM model-file format version, not the QP/C++ distribution version.

**Scope and attribution:** The QM file is a Quantum Leaps reference model. This experiment links to the upstream distribution rather than committing a copy of that model to this repository. The newer `qpcpp-examples` GitHub tree was observed to contain a `dpp.qm` with a different model-format version (`7.0.4`); it is **not** the verified input for this experiment.

**Verification limitations:** This records the user's reported byte comparison, not an independently reproduced download or cryptographic digest. A SHA-256 hash of the archived file may be added later to make the input fingerprint explicit.

## Collaboration model

The intended collaboration input is the independently authored `examples/DPP.collab` from the user's working tree. Its exact committed revision must be recorded once added to the branch. Do not replace it with a reconstruction from the QM model.

## Inspection protocol (planned)

1. Freeze the two input revisions and document provenance.
2. Inspect the `.collab` and `.qm` models only; do not rely on generated C++ during the initial inspection.
3. Record each claim with the relevant model element, evidence, assumptions and classification: satisfied, missing, unexpected or undetermined.
4. Distinguish a handler's presence in a state hierarchy from proof that an event is delivered to it.
5. Derive general validation rules, implement executable checks and compare their output with the human/AI inspection.
6. Retain unresolved questions and corrected findings in the report.

## Status

- QM provenance: **documented; byte comparison reported successful**.
- Collaboration source revision: **pending commit/confirmation**.
- Model inspection: **not started**.
- Cross-model validator: **not yet implemented for this experiment**.
