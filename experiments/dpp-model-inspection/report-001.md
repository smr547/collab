# DPP model inspection — Report 001

**Status:** Complete — experimental findings recorded; DSL extension proposed separately in [ADR-0015](../../docs/Decisions/ADR-0015-external-actors-and-system-boundary-interactions.md).

## Inputs

- **QM behavioural model:** Quantum Leaps QP/C++ 7.3.2 archive, `qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm`. Source and byte-comparison procedure are documented in [README.md](README.md).
- **Collaboration contract:** independently authored [`examples/DPP.collab`](https://github.com/smr547/collab/blob/8779714/examples/DPP.collab); committed at `8779714`.

## QM input fingerprint

The user supplied the verified historical `dpp.qm` directly for inspection. The uploaded XML is 17,637 bytes, with SHA-256:

`9f64c20dfac53fae16d053c33be4b810f5d999fe6bcec45a3d68a75129798c46`

Its root declares `<model version="5.3.0" links="1">`. This fingerprint identifies the uploaded inspection input; the independently reported byte comparison establishes its relationship to the QP/C++ 7.3.2 archive.

## Preliminary observations (historical investigation notes)

- The QM model declares `Philo` and `Table` active-object classes.
- `Philo` subscribes to `EAT_SIG` and `TEST_SIG`; `Table` subscribes to `DONE_SIG`, `PAUSE_SIG`, `SERVE_SIG` and `TEST_SIG`.
- `Philo` posts `HUNGRY_SIG` to `AO_Table` on entering `hungry`.
- `Philo` publishes `DONE_SIG` when exiting `eating`; `Table` publishes `EAT_SIG` when granting permission.
- `Philo` has `DONE` handlers despite not subscribing to `DONE_SIG`. These handlers assert that any received `DONE` event is for another philosopher; this is not evidence of an incorrect route. A handler's existence does not imply that an event is delivered to it.
- `TIMEOUT_SIG` is bound to `Philo::m_timeEvt`.

These observations preceded the executable inspection passes; their results are recorded below.

## Method

Compare only the `.collab` and `.qm` source models in the first inspection pass. Do not use generated C++ to settle ambiguous findings at this stage. Classify findings as **satisfied**, **missing**, **unexpected**, or **undetermined** and identify evidence and interpretation separately.

## Findings

The completed findings and scope limitations are consolidated in the conclusion below. The following sections preserve the sequence of experimental passes and their earlier provisional interpretations.

## Signal-by-signal comparison — inspection pass 1

The `.collab` model uses signal names without `_SIG`; the QM model uses `*_SIG` enumerators and transition triggers without the suffix. The correspondence below is a **proposed normalization** to test, not a general language rule.

| Collaboration declaration | QM evidence | Assessment |
| --- | --- | --- |
| `Philosopher -> Table: HUNGRY` | `Philo.hungry` entry constructs `HUNGRY_SIG` and calls `AO_Table->POST(pe, this)`; `Table.serving` and `Table.paused` handle `HUNGRY`. | **Satisfied**, subject to mapping `Philosopher` to `Philo`. Direct posting supports the destination. |
| `Philosopher -> Table: DONE` | `Philo.eating` exit publishes `DONE_SIG`; `Table` subscribes to `DONE_SIG` and handles `DONE` in serving and paused states. `Philo` also has defensive `DONE` handlers but does not subscribe to `DONE_SIG`. | **Satisfied**, subject to active-object name mapping and pub/sub interpretation. No evidence of delivery to `Philo` merely from its handlers. |
| `Table -> Philosopher: EAT` | `Table.serving` publishes `EAT_SIG` when forks are granted; `Philo` subscribes to `EAT_SIG` and handles `EAT` (notably in hungry state). | **Satisfied**, subject to active-object name mapping and pub/sub interpretation. Broadcast signal has a `philoId` payload; it is not point-to-point addressing. |
| `PhilosopherTimer -> Philosopher: TIMEOUT` | `Philo` constructor initializes `m_timeEvt(this, TIMEOUT_SIG, 0U)`; thinking/eating entries arm the time event and their `TIMEOUT` transitions are defined. | **Satisfied** as an internal timer delivery, subject to mapping the abstract timer name to `m_timeEvt`. |

### Semantic distinctions and scope

1. `Philosopher` in the collaboration model and `Philo` in QM are **not identical identifiers**. The comparison above explicitly assumes an alias. The validator must either accept a documented mapping or report the unresolved name mismatch; it must not silently equate names.
2. `DONE_SIG` and `EAT_SIG` use QP publish/subscribe, not direct `POST` to a named recipient. A collaboration arrow describes an intended communication relationship, not necessarily the transport primitive. The validator must establish subscription and emission, not infer direct addressing.
3. QM includes `PAUSE_SIG`, `SERVE_SIG` and `TEST_SIG` originating outside these declared collaborations. Whether these are omissions depends on the intended boundary of the `.collab` contract. They are **out-of-scope / undetermined**, not automatically defects.
4. This pass inspects QM model XML and the collaboration declaration, not compiled/generated C++. Dynamic runtime ordering, reachability and all possible event deliveries are not proven.
5. The `Philo` handlers for `DONE` and `EAT` in other states include assertions about `philoId`; they should not be treated as independent inbound collaboration edges.

### Candidate executable validation rules

- **V1 — AO identity resolution:** resolve declared collaboration participants against QM active objects using explicit mappings; report unmapped identifiers.
- **V2 — Direct-post edge:** where QM code creates signal `S` and posts to a known AO, verify a compatible collaboration edge and recipient trigger.
- **V3 — Pub/sub edge:** where QM code publishes signal `S`, derive possible recipients from subscriptions, then check corresponding collaboration edges and handlers; distinguish publication from delivery to a particular instance.
- **V4 — Timer edge:** match a QM `QTimeEvt` bound to an owner AO and signal with a declared timer-to-AO edge; do not infer a separately instantiated active object.
- **V5 — Coverage boundary:** distinguish undeclared signals from definite contract violations until the contract's completeness policy is specified.
- **V6 — Evidence reporting:** for every result, retain XML element, code fragment, rule, assumptions and confidence/status.

## Original investigation plan (completed)

1. Identify the exact `DPP.collab` input.
2. Inspect the verified QM source and capture specific state/handler/action evidence.
3. Produce a structured inspection matrix and implement bounded executable checks.

## Executable inspection results — first pass (user-run)

On branch `feature/dpp-model-inspection`, the user ran the first-pass tests and inspected the verified QP/C++ 7.3.2 `dpp.qm` with the explicit alias `Philosopher=Philo`.

- `python3 -m unittest discover -s tests -p 'test_qm_inspection.py'`: **4 tests passed**.
- `python3 src/collabc.py examples/DPP.collab --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm --qm-map Philosopher=Philo --check`: **3 PARTIAL, 1 UNDETERMINED, 0 MISSING**.
- `HUNGRY`, `DONE`, `EAT`: declared signal and receiver trigger observed; no end-to-end delivery assertion.
- `TIMEOUT`: deliberately undetermined by the first pass.

## Delivery-pattern inspection — second pass (implementation)

An **optional**, experimental `--qm-delivery` pass has been added to `collabc.py` in `src/qm_delivery.py`. It inspects QM XML code blocks for:
- locally constructed `Q_NEW(..., SIGNAL_SIG)` followed by `AO_Receiver->POST(...)`;
- locally constructed `Q_NEW(..., SIGNAL_SIG)` followed by `PUBLISH(...)`, plus `subscribe(SIGNAL_SIG)` in the receiver's QM class;
- a `QTimeEvt` constructor binding `m_timeEvt(this, SIGNAL_SIG, ...)` to its owner.

This is **source-pattern evidence**, not a C++ parser, proof of runtime delivery, or an exhaustive semantic analysis. Ambiguous or unrecognized source patterns remain `UNDETERMINED`. The output `SUPPORTED` does not imply complete satisfaction of the collaboration contract. The first pass remains unchanged unless `--qm-delivery` is requested.

Reproduce on StevenLaptop:

```bash
python3 -m unittest discover -s tests -p 'test_qm_*.py'
python3 src/collabc.py examples/DPP.collab \
  --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm \
  --qm-map Philosopher=Philo --qm-delivery --check
```

**Execution status:** These second-pass tests and the real DPP delivery run are committed but have not yet been run in the user's environment. Record actual output here before interpreting the findings.

## Second-pass run and regression (user-run)

The user ran nine tests successfully. On the historical QP/C++ 7.3.2 QM model, the delivery inspector reported **SUPPORTED** for `HUNGRY` and `TIMEOUT`, but **UNDETERMINED** for `DONE` and `EAT` because it did not recognize the receiver subscriptions.

Inspection of the uploaded XML established the cause: `subscribe(EAT_SIG)` in `Philo` and `subscribe(DONE_SIG)` in `Table` occur inside QM `<action>` elements. The original source-block collector did not include that element type. This was an **inspector coverage defect**, not evidence of missing DPP subscriptions.

The source-block collector now includes `action`, and the synthetic regression fixture represents subscriptions in nested `<initial><action>...` nodes. **The corrected version awaits a new user-side test run** before we claim all four edges supported on the reference model.

## Reverse coverage experiment (implementation; awaiting execution)

An opt-in `--qm-reverse` inspection discovers QM relationships independently of the collaboration declarations and compares directed triples (sender, receiver, signal). It recognizes locally constructed events delivered through direct `AO_X->POST`, `PUBLISH` combined with subscriptions, and locally bound `QTimeEvt` instances. Multiple subscribers produce multiple relationships. The categories `COVERED`, `UNDECLARED` and `UNRESOLVED` are **advisory**, and `UNDECLARED` does not currently fail `--check`.

This is a bounded source-pattern inventory, **not** a proof of exhaustive communications. In particular, event allocation/delivery split across different QM code blocks, externally generated events (such as BSP inputs), alternative posting syntax, and unknown AO targets may remain unresolved or invisible. A missing discovered relationship cannot establish that the implementation lacks one. Nor does the inventory prove that Table never emits DONE.

Reproduction:

```bash
python3 -m unittest discover -s tests -p 'test_qm_*.py'
python3 src/collabc.py examples/DPP.collab \
  --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm \
  --qm-map Philosopher=Philo --qm-delivery --qm-reverse --check
```

**Status:** Code and synthetic regression tests committed. Actual reverse findings on the original QP/C++ 7.3.2 QM file must be captured from the user's run, not presumed.

## Signal evidence inventory — fourth experimental view

User reproduced **12 passing tests** and a reverse inventory of **4 covered, 0 undeclared, 0 unresolved** routes on the historical QM model. This is the complete set of **recognized routes**, not an exhaustive inventory of signal usages. In particular, `PAUSE`, `SERVE` and `TEST` subscriptions are known from the source but do not appear in that route inventory.

The opt-in `--qm-signals` pass now reports QM `AppSignals` declarations, `Q_NEW` allocation sites, `subscribe` calls, transition triggers and `m_timeEvt` bindings **independently**, retaining evidence even where no sender can be identified. `NOT_IN_COLLAB` compares signal identities only and is not an error; it does not yet imply a complete communication route or determine whether an external participant belongs in the contract.

Run:

```bash
python3 -m unittest discover -s tests -p 'test_qm_*.py'
python3 src/collabc.py examples/DPP.collab \
  --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm \
  --qm-map Philosopher=Philo \
  --qm-delivery --qm-reverse --qm-signals --check
```

**Awaiting historical-model execution.** The signal inventory is source-pattern evidence only. It does not scan BSP C/C++ source, prove absence of emitters, or infer publishers from subscriptions. A later common evidence model should unify these separate views without losing the distinction between signal declaration, usage and established delivery.

## Reconciliation of historical QM signal and route totals

The user reproduced **14 passing tests**. The first signal inventory reported 10 signal-like identifiers, 6 not in the collaboration, while the reverse route inventory reported 4 covered and 0 undeclared. These are **different denominators**, not contradictory counts: signal identities include subscriptions with unknown origins; discovered routes require evidence of sender and receiver.

Three of the six reported absent identifiers were **enum sentinels** (`Q_USER_SIG`, `MAX_PUB_SIG`, `MAX_SIG`), not application communication signals. The inventory has been corrected to exclude these sentinels from the `AppSignals` scan, with regression assertions.

Expected application signal totals on this QM input: **7 signal identities**; **4 represented in the collaboration** (`HUNGRY`, `DONE`, `EAT`, `TIMEOUT`); **3 not represented** (`PAUSE`, `SERVE`, `TEST`). The reverse inventory remains **4 recognized routes covered, 0 additional complete routes recognized**. These totals are not a completeness proof; the three extra signal identities require source-boundary investigation. Corrected output awaits user-side execution.


## Conclusion — Report 001 complete (16 October 2026)

**Result:** The original four collaboration routes have supporting source-pattern evidence in the historical QM file: `HUNGRY` (direct POST), `DONE` and `EAT` (publish/subscribe), and `TIMEOUT` (time-event binding). Reverse QM inspection discovers four covered routes and no additional complete routes *within its recognized patterns*. This is not an exhaustive proof of the application.

**Reproduced by the user:** On branch `feature/dpp-model-inspection`, after pulling commit `9c5d8b9`, `python3 -m unittest discover -s tests -p 'test_qm_*.py'` completed **14 tests, OK**. The historical-model invocation

```bash
python3 src/collabc.py examples/DPP.collab \
  --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm \
  --qm-map Philosopher=Philo \
  --qm-signals --qm-reverse --check
```

reported **0 MISSING** in pass 1 (3 PARTIAL, 1 UNDETERMINED); an application-signal inventory of **7 signal identities**, **4 represented** and **3 not represented** (`PAUSE_SIG`, `SERVE_SIG`, `TEST_SIG`); and reverse inventory **4 COVERED, 0 UNDECLARED, 0 UNRESOLVED**. The corrected inventory excludes the enum sentinels `Q_USER_SIG`, `MAX_PUB_SIG` and `MAX_SIG`. Earlier “awaiting execution” statements in the chronological sections above are superseded by these results. A separate earlier user run of `--qm-delivery` supported all four contract routes.

### Evidence beyond QM: BSP and QSpy

The public QP/C++ 7.3.2 NUCLEO-L152RE **QV** `qv/bsp.cpp` shows B1 (PC13) sampled and debounced in `SysTick_Handler`. Depressing B1 publishes a static `PAUSE_SIG` event; releasing it publishes `SERVE_SIG`. Table subscribes to both. The BSP also directly posts a static `TEST_SIG` event to `AO_Table` from `EXTI9_5_IRQHandler`. The supplied file does not establish what stimulates that interrupt; no TEST runtime delivery was observed. Philosopher's subscription to TEST does not imply this direct-posted TEST reaches Philosopher.

The user's QSpy trace establishes, for one observed execution:

| Input / signal | Runtime evidence | HSM result |
| --- | --- | --- |
| B1 pressed / PAUSE_SIG | SysTick publication, post to Table, queue get and dispatch | `Table::serving -> Table::paused`; `PAUSED_STAT 1` |
| B1 released / SERVE_SIG | SysTick publication, post to Table, queue get and dispatch | `Table::paused -> Table::serving`; `PAUSED_STAT 0` |

While paused, Table continued to dispatch HUNGRY and DONE events; pausing Table does not halt every AO. QSpy instrumentation timestamps for publication and post are not strictly ordered in the displayed trace, so a future runtime correlator must not rely solely on printed timestamp monotonicity. These observations corroborate the BSP-originated routes but do not establish exhaustive behaviour.

### QSpy as an independent collaboration-validation input

The B1 experiment reveals an additional use for QSpy beyond corroborating source inspection: **a validator can compare an observed QSpy execution trace directly with the `.collab` communication contract, without needing the QM model or BSP source as inputs**. For example, the captured `PAUSE_SIG` and `SERVE_SIG` publications and Table deliveries are not declared in the original four-route `examples/DPP.collab`. A trace-only inspection could therefore flag them as **observed but undeclared** communication, prompting a review of the contract's intended system boundary. It should not automatically label them implementation defects.

A candidate trace-only classification is:

| Trace/contract relationship | Interpretation |
| --- | --- |
| Declared and observed | Supported for the recorded execution, not universally proven |
| Observed but undeclared | Unexpected relative to the contract; investigate model scope and event provenance |
| Declared but unobserved | Not exercised or not visible in this trace; not evidence of absence |
| Attribution or coverage uncertain | Undetermined; do not infer an endpoint or violation |

A future validator must resolve QSpy signal and object dictionaries, distinguish publication from per-recipient delivery, avoid treating publisher identity and eventual recipient as interchangeable, and account for incomplete/filtered traces. The recorded `QF-Pub` and `AO-Post` timestamps are not strictly ordered in the displayed output, so timestamp monotonicity alone is insufficient for correlation. In particular, a `QF-Pub` record does not establish every subscriber's delivery; the observed Table `AO-Post`/`AO-GetL` records supply separate evidence.

**Disposition:** This is an experimentally motivated validator capability, **not an implemented or tested trace validator**. Report 002 may use the unchanged `DPP.collab` and the captured QSpy trace to prototype detection of PAUSE/SERVE as undeclared routes, then evaluate how a boundary-aware model changes the result.

### Architectural finding and disposition

**QM is not the whole executable system boundary.** Human interaction with B1 is translated by BSP/SysTick into application signals absent from the QM-only communication inventory. This is a source-coverage limitation of the inspection approach and a concrete motivation for expanding the `collab` language's modelling scope. It is **not** a validated defect in QM or the current `DPP.collab`.

[ADR-0015 — External Actors and System-Boundary Interactions](../../docs/Decisions/ADR-0015-external-actors-and-system-boundary-interactions.md) records the proposed architectural direction without prescribing DSL syntax. Report 002 should evaluate actor/input/BSP/ISR representation and multi-source validation. The authoritative `examples/DPP.collab` is unchanged.

**Limits:** The QM inspectors use bounded source-pattern matching, not a full C++ parser or formal proof. QSpy proves only observed execution paths. This report records user-run tests and traces; no independent hardware test was executed by the report author.
