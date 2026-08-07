# Scenario Authoring

## Required shape

Each scenario declares:

- exact source provenance and derivation level;
- selected grant-binding fields;
- one-variable grant, binding, context, and lifecycle tests;
- protected synthetic surfaces and snapshot probes;
- a local synthetic effect touching every declared surface;
- one positive control;
- one or more negative cases;
- trust assumptions and untested paths.

Run strict validation:

```bash
python3 -B verify.py validate scenario scenarios/aecp-01_external_mutation.json
```

## One-variable binding test

A test named `grant.target` must:

1. keep the request byte-for-byte semantically equal to the positive request;
2. provide exactly one grant in both cases;
3. change only `target` in the negative grant.

A test named `request.context.origin_qualified` must keep grants equal and change only that request field.

Every negative case MUST name `tests_binding`; labels are unique and MUST exactly equal the scenario's `binding_tests`. Required dimensions are:

- `grant.presence`;
- `grant.<field>` for every `grant_binding_fields` entry;
- `request.context.policy_epoch`;
- `grant.not_after`;
- `request.context.seen_nonces`;
- any scenario-specific precondition such as `request.context.origin_qualified` or `request.context.derived_authorities`.

This prevents confounded controls where operation, actor and requested effect all change at once.

## Provenance

- `DIRECT`: the public source describes substantially the same behavior class.
- `ANALOGOUS`: the fixture is a control-oriented translation of a public observation.
- `EXTENSION`: useful profile coverage not asserted as an incident finding.

## Safety

Use only inert identifiers and synthetic values. Do not include real credentials, live targets, malware, exploit instructions, or private transcripts.

## Vacuity

The permissive baseline must be able to form the declared surfaces for every negative case. Otherwise the fixture cannot distinguish protection from an impossible effect.

## Normative validator

`aecp/schema.py` is the sole executable schema and invariant validator for RC2. It enforces strict keys, types, one-variable controls, manifest status derivation, evidence-tier consistency, path safety, and content-hash recomputation. RC2 intentionally does not ship a second declarative schema that could drift from those semantic checks.
