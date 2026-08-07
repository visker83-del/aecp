# Threat Model

## In scope

AECP v0.1 models a fallible or adversarial adapter that receives a structured request and the only handle to a local synthetic effect world. The adapter may:

- allow or deny correctly;
- deny but still emit;
- allow but fail to emit;
- ignore target, consumer, use, subject, origin, expiry, or replay scope;
- emit through an undeclared alternate synthetic surface;
- raise an exception or return invalid output.

The harness observes state changes independently of the adapter's reported decision.

## Trusted test components

- fixture loader and strict validator;
- policy-free synthetic world and effect port;
- before/after snapshot mechanism;
- `snapshot-diff-v1` observer;
- canonical JSON and digest implementation;
- runner and result validator.

## Harmless local boundary

Bundled fixtures make no public-network requests, contact no real people, use no credentials, modify no public service, and contain no malicious payload.

## Third-party adapter warning

Python adapters run in the harness process. Subprocess adapters run as the supplied command. Neither is sandboxed. Review third-party adapter code and run it in an appropriate isolated environment. The harmless claim applies to bundled code and fixtures, not arbitrary external adapters.

## Out of scope

RC2 does not prove:

- production-path mediation or host isolation;
- correctness or truth of authorization/evidence inputs;
- correctness of production policy;
- resistance to compromised root/admin keys;
- absence of side channels;
- absence of transient formation and rollback between before/after snapshots;
- semantic truth of model reasoning;
- production resilience, latency, availability, or performance;
- legal validity or scope of any patent;
- conformance of any Certum commercial implementation;
- resistance to an adapter deliberately hard-coded to the public fixtures or their deterministic request tokens.
- resistance to hostile in-process adapters that inspect or monkeypatch harness internals; use the subprocess bridge and external OS isolation when process separation matters.
