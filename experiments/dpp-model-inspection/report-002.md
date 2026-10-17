# DPP model inspection — Report 002: external participants and QM cross-validation

- **Date:** 2026-10-17
- **Status:** Observed on StevenLaptop; read-only validation
- **Branch:** `feature/external-participants`
- **Inputs:** `examples/DPP.collab` and historical QP/C++ 7.3.2 `dpp.qm`
- **Related:** ADR-0015, ADR-0016, ADR-0017; Report 001

## Purpose

Exercise the current collaboration validator against the historical DPP QM model, including the external `User` participant. Preserve the distinction between QM structural evidence, recognized source-pattern delivery evidence, and end-to-end runtime evidence. Neither model is changed by this report.

## Reproduction

From the root of a checkout of `smr547/collab` on `feature/external-participants`, with the historical QM source at the path shown:

```bash
python3 src/collabc.py examples/DPP.collab \
    --check \
    --qm ~/qp_old/qpcpp/examples/arm-cm/dpp_nucleo-l152re/dpp.qm \
    --qm-map Philosopher=Philo \
    --qm-delivery \
    --qm-signals \
    --qm-reverse
```

`--check` avoids generation of `.puml` and `.hpp` files. The explicit `Philosopher=Philo` mapping reconciles the historical QM class abbreviation without modifying either model. The historical QM file was previously identified in the QP/C++ 7.3.2 archive; its recorded SHA-256 is `9f64c20dfac53fae16d053c33be4b810f5d999fe6bcec45a3d68a75129798c46`. The command above does not independently verify that hash.

To reproduce the unit-test checkpoint:

```bash
python3 -m unittest discover -s tests -v
```

## Observed results

The user executed both commands on StevenLaptop on 2026-10-17 and supplied their terminal output.

| Inspection | Observed result |
| --- | --- |
| Parsed model | 4 participants, 3 collaborations, 6 distinct signals |
| QM identity/declaration/trigger pass | 0 missing; 1 undetermined (timer in first pass) |
| QM delivery source-pattern pass | 0 missing; 2 undetermined (external origins) |
| QM signal inventory | 7 QM application signals; 6 represented in Collab; `TEST_SIG` not represented |
| Reverse QM route inventory | 4 covered; 0 undeclared; 0 unresolved |
| Unit tests | 35 tests; `OK` |

### Edge-by-edge evidence

| Declared collaboration | QM structural pass | QM delivery pass |
| --- | --- | --- |
| `User -> Table PAUSE` | PARTIAL: `PAUSE_SIG` declared; Table handles PAUSE | UNDETERMINED: external origin/delivery requires other evidence |
| `User -> Table SERVE` | PARTIAL: `SERVE_SIG` declared; Table handles SERVE | UNDETERMINED: external origin/delivery requires other evidence |
| `Philosopher -> Table HUNGRY` | PARTIAL | SUPPORTED: `Q_NEW(HUNGRY_SIG)` and `AO_Table->POST` |
| `Philosopher -> Table DONE` | PARTIAL | SUPPORTED: publish from Philo; subscription in Table |
| `Table -> Philosopher EAT` | PARTIAL | SUPPORTED: publish from Table; subscription in Philo |
| `PhilosopherTimer -> Philosopher TIMEOUT` | UNDETERMINED: timer not checked by initial pass | SUPPORTED: `QTimeEvt` binding to `TIMEOUT_SIG`; arm/firing not proven |

The reverse inventory reported exactly these four QM-supported internal/timer routes as `COVERED`: `Philo -> Table HUNGRY`, `Philo -> Table DONE`, `Table -> Philo EAT`, and `<timer:Philo> -> Philo TIMEOUT`. The reverse pass does not discover BSP-originating `User` routes.

The QM signal inventory also identified `TEST_SIG`: declared in QM, subscribed to by Philo and Table, handled by both, but `NOT_IN_COLLAB`. Earlier DPP inspection (Report 001) associated its origin with the BSP interrupt handler. Its absence from the logical collaboration is a modelling question, **not** proof of an omitted route.

## Interpretation and limits

1. An `external User` is **not required** to have a QM class. The validator can inspect the receiving Table HSM without flagging the absent User class.
2. `PARTIAL` confirms declaration and receiver-trigger evidence, **not** delivery. `SUPPORTED` in the delivery pass denotes recognized QM source patterns, **not** runtime proof.
3. External `PAUSE` and `SERVE` routes remain `UNDETERMINED` in this command because BSP source and QSpy evidence are outside the present automated QM inspection. Report 001 contains separate BSP/runtime investigation.
4. The timer's initial `UNDETERMINED` and delivery-pass `SUPPORTED` are compatible: the latter pass recognizes a `QTimeEvt` binding, but not timer arming or firing.
5. `TEST_SIG` is an additional QM application signal, not an automatically required logical collaboration signal. The validator does not establish that its absence is correct.
6. The historical `DONE`, `PAUSE`, `SERVE`, and `Philo` identifiers remain unchanged. ADR-0017 records future vocabulary intent; this report does not claim a revised QM model exists.
7. No claim of complete behavioural equivalence, state-dependent reachability, or end-to-end signal delivery follows from these results.

## Conclusion

The current DPP collaboration and historical QM implementation have **no missing declarations/triggers** among the six modelled collaboration signals, and **no undeclared routes** among the four routes discovered by the conservative QM reverse inspector. The two external deliveries remain appropriately unverified. This is a reproducible validation checkpoint, not a proof of completeness.

The reported execution and 35-test result were supplied from the user's laptop; this report was committed remotely without rerunning those commands in the author's environment.
