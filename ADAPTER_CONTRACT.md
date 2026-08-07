# Adapter Contract 1.0

## Purpose

An adapter connects a candidate control to the AECP synthetic world. The adapter decides whether to request the declared local emissions. It does not report whether surfaces changed; the harness observes that independently.

## Python contract

A module factory named on the CLI MUST return an object with:

```python
def describe() -> dict:
    return {
        "api_version": "1.0",
        "id": "vendor-control",
        "version": "2026.08",
        "kind": "external-python",
        "description": "Short exact description"
    }

def handle(request: dict, port) -> dict:
    # Optionally request local synthetic writes:
    port.emit("surface-id", "key", {"synthetic": "value"})
    return {"decision": "ALLOW", "reason": "free-text reason"}
```

Run it with:

```bash
python3 -B verify.py run --adapter package.module:factory
```

The factory is called separately for each case so cases do not share hidden state.

## Request fields

The request includes:

- an opaque deterministic `request_token` (human-readable case/scenario labels are withheld from the adapter);
- `operation`, `target`, `consumer`, `use`, `subject`, `origin`;
- integer logical time `now`;
- strictly typed `context` preconditions defined by PROFILE §6.1;
- `grant_binding_fields`;
- `presented_grants`;
- `synthetic_effect.entries`.

Adapters may use different internal mechanisms. The fields are the portable exercise vocabulary, not a mandated production record format.

## Effect port

`port.emit(surface, key, value)` applies a local synthetic write. The port:

- knows no authorization policy;
- accepts any non-empty surface name so previously unknown bypasses remain observable;
- records content-addressed changes;
- does not return an authorization verdict.

The adapter MUST NOT claim that an effect did or did not form. Such fields are ignored.

A write to a surface outside the scenario declaration is retained and fails the case as an undeclared effect.

## Subprocess JSON-lines bridge

A subprocess reads one request JSON object line from standard input and MUST return exactly one non-empty JSON object line on standard output:

```json
{
  "decision": "ALLOW",
  "reason": "example",
  "emissions": [
    {"surface": "surface-id", "key": "key", "value": {"synthetic": true}}
  ]
}
```

Run it with:

```bash
python3 -B verify.py run \
  --adapter-label vendor-control-2026-08 \
  --adapter-command ./adapter-command --adapter-argument
```

Place `--adapter-command` last; the remaining tokens are passed as the command argv without platform-specific shell splitting. The label must be 1–128 ASCII letters, digits, dots, underscores, or hyphens and must start with a letter or digit. The label, not the command or its absolute path, is hashed into the manifest.

The child MUST exit `0`. Its response may contain only `decision`, optional non-empty `reason`, and optional `emissions`. The parent validates the complete response before applying any emission, then performs the independent snapshot diff. Diagnostic logs belong on standard error and are not part of the manifest. The subprocess is untrusted executable code and is not sandboxed by AECP.

## Failure semantics

Exception, timeout, malformed output, or invalid decision with no observed effect produces `INCONCLUSIVE`. An effect observed before an error is a failure with `FORMED_DURING_ERROR`; the error cannot erase formation evidence.
