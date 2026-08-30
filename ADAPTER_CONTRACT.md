# Adapter Contract 1.0

## Purpose

An adapter connects a candidate control to the AECP synthetic world. It reports the candidate's decision and routes every synthetic effect the exercised candidate path attempts through the effect port. It MUST NOT create, suppress, or infer emissions from the decision it is about to return. It does not report whether surfaces changed; the harness observes that independently.

If you are wrapping an external control rather than writing a self-contained example, read [Wrapping an external control](#wrapping-an-external-control) before anything else. The most common integration mistake produces a result that looks like a pass and measures nothing.

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
    # Forward only the effects the candidate's actuation path attempted.
    # Never derive this from the decision you are about to return.
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

## Wrapping an external control

The bundled adapters are self-contained illustrations: the control and the synthetic
actuation are the same code, so `if allowed: emit` is correct there. It is not a template
for wrapping something external.

A wrapper that derives emissions from the decision looks like this:

```python
decision = candidate.authorize(request)
if decision == "ALLOW":
    emit_declared_effect()      # wrong: the emission is the decision, restated
```

That wrapper still exercises qualification — a candidate that wrongly allows a negative
case, or wrongly denies the positive control, is still caught. What it can never produce
is either off-diagonal observation: a denial that formed an effect, or an allowance that
formed nothing. Those two are the reason AECP exists. A pass from such a wrapper says the
decisions were right; it does not say the effect path was controlled, and it must not be
reported as though it did.

Route the candidate's own actuation attempts instead:

```python
attempted = []
decision = candidate.run(request, on_effect=attempted.append)
for entry in attempted:
    port.emit(entry["surface"], entry["key"], entry["value"])
return {"decision": decision, "reason": reason}
```

`on_effect` stands for whatever hook, callback, or interceptor your control already uses
at the moment it is about to act. If your control cannot surface an attempted effect
independently of its decision, AECP cannot evaluate effect-path non-formation for that
integration. Report that rather than a pass.

### Checking your own wiring

A correctly wired and a circularly wired integration can both pass while the candidate
behaves correctly. The difference only shows when the candidate misbehaves, so make it
misbehave on purpose, inside the candidate's actuation path rather than in the adapter.
Two faults, catching two different miswirings:

| Injected fault | Expected | Catches |
|---|---|---|
| act on a request the candidate denied | `DENIED_BUT_FORMED` | an adapter that suppresses emissions when the decision is `DENY` |
| act on nothing after the candidate allowed | `ALLOWED_BUT_NOT_FORMED` | an adapter that fabricates emissions on the allow path |

A circular wrapper passes both, because it never let the candidate's behaviour reach the
port in the first place.

If you cannot make the run fail either way, the integration is not connected to the effect
path and the passing result does not mean what it appears to mean.

`examples/subprocess_adapter.py` is a runnable version of both halves; see
[`examples/README.md`](examples/README.md).

## Failure semantics

Exception, timeout, malformed output, or invalid decision with no observed effect produces `INCONCLUSIVE`. An effect observed before an error is a failure with `FORMED_DURING_ERROR`; the error cannot erase formation evidence.
