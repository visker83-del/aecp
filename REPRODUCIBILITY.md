# Reproducibility

## Levels

- **R0 — not established:** a result cannot be reproduced from the published material.
- **R1 — same-environment deterministic:** repeated runs produce byte-identical manifests.
- **R2 — cross-platform deterministic:** supported operating-system/Python combinations produce the same `content_sha256`.
- **R3 — independent reimplementation:** another implementation reproduces the canonical fixture and result semantics without reusing the reference runner.

RC2 claims **R1** for the bundled self-test. CI exercises Python 3.11–3.13 on Linux, macOS, and Windows as an R2 candidate, but R2 should be claimed only after the public CI matrix completes and its digests are compared.

R3 is an external milestone, not a bundled claim.

## Deterministic content

The hashed manifest content contains no wall-clock timestamp, hostname, duration, absolute path, or floating-point value in the bundled fixtures/results. Fixtures use integer logical time. A subprocess result hashes the caller-supplied restricted ASCII adapter label, never the executable command or absolute path.

`content_sha256` is SHA-256 over canonical JSON with:

- UTF-8;
- sorted object keys;
- no insignificant whitespace;
- no NaN or Infinity;
- arrays preserved in authored order.

Pretty-printed manifest bytes are also deterministic. Runtime metadata, if collected externally, is outside the hashed content.

## Fixture digests

Each result includes:

- `fixture_file_sha256`: exact published bytes;
- `fixture_canonical_sha256`: semantic JSON digest independent of formatting.

## Independent reproduction vocabulary

Do not call a simple `./verify.sh` run an independent implementation reproduction. Use:

- **R0-run:** third party runs the bundled self-test;
- **R1-port:** third party independently ports fixture semantics;
- **R2-adapter:** third party connects its own adapter and publishes the exact manifest;
- **R3-counterexample:** third party produces an executable missing/alternate path.

Strategic evidence should distinguish these levels explicitly.
