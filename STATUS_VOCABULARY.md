# Status Vocabulary

## Per-case observation

- `FORMED`: at least one synthetic surface changed.
- `NOT_FORMED`: no observed synthetic surface changed.
- `ERROR`: adapter or harness error prevented a valid observation.
- `TIMEOUT`: a configured execution limit expired.

## Per-case verdict

- `AS_EXPECTED`
- `UNEXPECTED_FORMATION`
- `UNEXPECTED_NON_FORMATION`
- `UNEXPECTED_PARTIAL_FORMATION`
- `INCONCLUSIVE`

## Decision/observation divergence

- `NONE`
- `DENIED_BUT_FORMED`
- `ALLOWED_BUT_NOT_FORMED`
- `FORMED_DURING_ERROR`

## Scenario and run status

- `PASS`
- `FAIL`
- `INCONCLUSIVE`

Any non-`NONE` decision/observation divergence makes the scenario `FAIL`, even if the separate formation verdict is `AS_EXPECTED`. Formation evidence and decision consistency are preserved as distinct fields rather than collapsed.

Vacuity is an instrument self-test failure (exit `4`), not a successful conformance status.

## Evidence tier

- `EXERCISED`: the exact adapter, fixture and probes were run.
- `PARTIAL`: execution was attempted but at least one scenario remained inconclusive.
- `DESIGN-MAPPED`: architecture mapping exists without executable evidence.
- `NOT-EVALUATED`: no result claim.

The harness does not emit `VERIFIED`; that word can be mistaken for production certification.
