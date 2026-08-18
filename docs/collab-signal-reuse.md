# Signal-reuse compiler update

This patch implements ADR-0003's initial receiver-centric signal-reuse rule.

## Behaviour

Legal:

```text
A -> C
    EVENT_READY

B -> C
    EVENT_READY
```

This is one semantic signal with two routes and generates one C++ enum member.

Rejected:

```text
A -> C
    EVENT_READY

B -> D
    EVENT_READY
```

because the same name is being used for different receivers.

The patch also rejects accidental duplicate occurrences within one directional flow.

## Apply

From the root of the `collab` repository:

```bash
git status
git apply --check collab-signal-reuse.patch
git apply collab-signal-reuse.patch
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

Then try the Rain Gauge model which motivated ADR-0003:

```bash
python3 src/collabc.py /path/to/rain-gauge.collab
```

The expected summary counts **semantic signal identities**, not route occurrences.

For example, if `BUCKET_SWITCH_CLOSING` appears on two routes, it contributes one signal to the `signal(s)` count and one member to the generated enum, while remaining visible on both routes in generated PlantUML.
