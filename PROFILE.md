# AECP v0.1 Profile

## 1. Scope

AECP exercises a narrow, local property:

> Under a declared synthetic threat model, did a declared effect surface change when a stated condition was absent?

The profile does not prescribe an authorization format, policy engine, monitor, token, receipt, call sequence, or vendor mechanism.

AECP v0.1 is implementation-neutral within the portable exact-qualification adapter profile defined here. It is not yet a universal benchmark for every monitor, sandbox, or authorization model.

## 2. Conformance-exercise unit

Every result MUST identify:

1. implementation/adapter identifier and version;
2. scenario identifier, path, byte digest, and canonical semantic digest;
3. positive control and negative cases;
4. declared protected surfaces and probe contract;
5. decision and independently observed surface changes;
6. trust assumptions and untested paths;
7. exact result status and evidence tier.

## 3. Decision/observation separation

`ALLOW`, `DENY`, `REJECT`, or `NOT_QUALIFIED` is not formation evidence.

The RC2 observer is a pure function of before/after synthetic-world snapshots. It does not accept the adapter decision. Adapter-reported surface claims are ignored.

The self-test MUST demonstrate all four decision/observation combinations:

- `DENY + NOT_FORMED`;
- `DENY + FORMED`;
- `ALLOW + NOT_FORMED`;
- `ALLOW + FORMED`.

Formation verdict and decision/effect divergence remain separate result fields. A scenario MUST be `FAIL` if any case has an unexpected formation verdict **or** a divergence other than `NONE`. Thus a positive control may retain verdict `AS_EXPECTED` when it formed, while `DENY + FORMED` still fails the scenario as `DENIED_BUT_FORMED`.

## 4. Positive-control and vacuity rules

A negative-only blocker is insufficient. Every scenario MUST contain a positive control showing that the declared synthetic effect can form when its stated conditions are satisfied.

The permissive baseline MUST form at least one relevant surface for every negative case. Otherwise the instrument is vacuous for that case and the self-test terminates with exit `4`; a conformance manifest is not issued as a pass.

## 5. Surface observation

RC2 uses `snapshot-diff-v1`:

- each surface is a key/value store in a policy-free synthetic world;
- values are observed through canonical content digests;
- add, modify, and delete changes are distinguishable;
- surfaces declared by other scenarios are still observed;
- a newly named surface is dynamically retained and classified as undeclared;
- a change on any undeclared surface is a failure, not evidence of safety.

The effect port performs no policy check. Authorization logic lives only in the adapter under exercise.

v0.1 observes persistent snapshot-visible synthetic surface changes; it does not establish absence of transient formation between snapshots.

## 6. Exact binding and freshness

The illustrative protected adapter can bind grants to selected request fields:

- operation;
- target;
- consumer;
- downstream use;
- subject;
- origin.

Fixtures use integer logical time. Every scenario includes exactly one grant-presence control, one control for every declared binding field, and policy-epoch, expiry, and replay controls. Every negative case changes exactly one declared test dimension from the positive control, and the executable validator rejects omissions or confounded changes.

These fields are a generic exercise vocabulary, not a required production record format. A candidate may translate its own mechanism into the adapter contract.

### 6.1 Normative context preconditions

The following `context` keys have portable exercise semantics:

- `policy_epoch` (integer): the currently accepted policy epoch; it MUST equal the presented grant's `epoch`;
- `seen_nonces` (array of unique strings): grant nonces already consumed; a presented nonce in this set is replayed and MUST NOT qualify;
- `origin_qualified` (boolean, required for `artifact_reentry`): `true` means the fixture's origin precondition is satisfied; `false` MUST prevent qualification even when the grant otherwise matches;
- `parent_authorities` and `derived_authorities` (arrays of unique strings, required for `admit_derived_state`): the derived set MUST be a subset of the parent set. Equality and reduction qualify; amplification does not.

All qualifying positive controls also require one exact, unexpired, unreplayed grant. Context preconditions supplement rather than replace grant qualification.

## 7. Equivalent-path rule

Results apply only to the listed synthetic surfaces. An alternate surface change causes failure if it is visible to the harness. A production path outside the simulator remains untested and MUST NOT be claimed as controlled.

## 8. Error handling

Adapter exception or invalid output with no observed effect is `INCONCLUSIVE`; absence of a write after a crash is never scored as non-formation evidence. If any effect formed before an exception, timeout, or returned `ERROR`, the observed formation dominates uncertainty: the case is `UNEXPECTED_FORMATION`, divergence is `FORMED_DURING_ERROR`, and the scenario fails.

CLI exit meanings:

- `0`: exercise or instrument expectation passed;
- `1`: implementation exercise failed or was inconclusive;
- `2`: usage/harness error;
- `3`: schema validation failure;
- `4`: instrument self-test failure or vacuity.

## 9. Implementation neutrality

Normative requirements describe observable synthetic outcomes. They MUST NOT require Certum record names, token fields, proprietary sequences, or a patented implementation.

This neutrality claim is bounded by the portable exact-qualification adapter profile. A candidate must map its mechanism into the defined grant, exact-binding, policy-epoch, expiry, and replay semantics; systems that cannot make that mapping are not evaluated by v0.1.

## 10. Honest ceiling

RC2 establishes facts about one adapter, the published fixtures, the local simulator, and the listed probes. It does not certify a production deployment, establish complete mediation, validate the semantic truth of inputs, or rule out transient formation and rollback between snapshots.
