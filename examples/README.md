# Connecting your own control

`subprocess_adapter.py` is a working adapter you can copy. It wraps a stand-in control
(`ExampleCandidate`); replace that with a call into yours and leave the adapter half alone.

The language does not matter. The subprocess bridge reads one JSON request line on stdin
and writes one JSON response line on stdout, so any language works. This example is Python
only because the repository already is.

## 1. Run it as shipped

```bash
python3 -B verify.py run \
  --adapter-label example-subprocess \
  --adapter-command python3 examples/subprocess_adapter.py
```

Seven scenario classes, `PASS`, exit `0`.

## 2. Check that your wiring is real

This is the step that matters, and it is the one that is easy to skip.

A correct integration and a broken one both pass the run above. The difference only shows
when the control misbehaves. So make it misbehave:

```bash
AECP_EXAMPLE_FAULT=leak-after-deny python3 -B verify.py run \
  --adapter-label example-subprocess-fault \
  --adapter-command python3 examples/subprocess_adapter.py
```

Expected: `FAIL`, non-zero exit, and `divergence=DENIED_BUT_FORMED` on the negative cases.

The fault is injected inside the candidate's actuation path, not in the adapter. That is
deliberate. Putting the fault in the adapter would only prove the adapter reaches the
effect port; it would not prove the adapter reaches your control.

**If you cannot make your own integration fail this way, it is not connected to the effect
path.** The passing result then tells you the decisions were right. It does not tell you
the effect stayed absent, which is the question this profile exists to ask.

## 3. Swap in your control

Two things change:

- `ExampleCandidate._decide` becomes a call into your control's decision path.
- `ExampleCandidate.run`'s `on_effect` becomes whatever hook your control already has at
  the moment it is about to write, send, or act.

The adapter half stays as written. In particular, `handle()` builds emissions from what
the candidate attempted and never reads `decision` to decide what to emit. Keeping that
separation is the whole point.

If your control has no way to surface an attempted effect independently of its decision,
stop here. AECP cannot evaluate effect-path non-formation for that integration, and the
honest report is that it could not be connected — not a pass.

## 4. Field mapping

The request vocabulary (`operation`, `target`, `consumer`, `use`, `subject`, `origin`,
`presented_grants`, `context`) is a portable exercise format, not a required production
record. Map your own fields onto it and write down the assumptions you made; a reader of
your result needs them to know what was actually tested.

Two operations carry an extra dimension, handled in `_decide`:

- `artifact_reentry` — `context.origin_qualified` must be true
- `admit_derived_state` — `context.derived_authorities` must be a subset of
  `context.parent_authorities`

## 5. If you publish a result

Publish it in your own repository and link it from an AECP issue. There is no central
list and no certification.

Include the AECP source revision, your adapter label and control version, the exact
command, the result manifest and its `content_sha256`, the field-mapping assumptions from
step 4, and the wiring check from step 2 reported separately from the conformance run —
the wiring check is a deliberately induced failure that proves the instrument is
connected, not a finding about your product.

State plainly what the result does not establish: production paths outside the synthetic
effect port, complete mediation, and any effect that formed and was rolled back between
snapshots.
