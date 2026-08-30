# AEB-04 Interoperability Mapping

> **Status: non-normative interoperability mapping.** This note records a
> version-pinned mapping and local exercise. It does not add an AECP stable
> scenario, make AEB an AECP dependency, certify an AEB implementation, or
> establish that AEB as a whole has passed AECP.

## Identification

- External mechanism: Action Evidence Boundary (AEB)
- External revision: [`draft-schrock-action-evidence-boundary-04`](https://datatracker.ietf.org/doc/html/draft-schrock-action-evidence-boundary-04)
- Reviewed local posted-text digest:
  `sha256:23d4daa5e436c4dc321c5e21e75f20965c6430c9807a3007e9c84762d33df63f`
- AECP profile: portable exact-qualification profile `0.1-rc2`
- AECP repository baseline: `v0.1-rc2.1`
- AECP source revision exercised:
  `43832fa87213826036c6f0b0e4642c6084088565`
- Mapping proposal and review: [issue #1](https://github.com/visker83-del/aecp/issues/1)
- Substantive contributor: Iman Schrock, EMILIA Protocol, Inc.
- Last validated: 2026-08-29 against the revisions above

Issue #1 predates AEB revision `-04`. The exact examples from that issue were
therefore checked again against both the current AEB text and current AECP
`main`. AEB `-04` makes the material-action limit especially important: an AEB
boundary must construct the observed action from boundary-controlled facts,
include every field declared material by the pinned action-type definition,
and recompute or map the CAID without guessing. The AECP examples below bind
only the portable fields they explicitly name.

## Purpose and layer boundary

AEB defines an ordered executor-side lifecycle: native verification, exact
material-action matching, evidence-requirement satisfaction, local
authorization, durable consumption or reservation, invocation, outcome
classification, and authenticated reconciliation. AECP asks a narrower
question: after an adapter decides, did a declared or dynamically emitted
synthetic surface change between the observer's before and after snapshots?

This mapping shows that three AEB-shaped failure questions can be expressed in
AECP's current portable profile:

1. a presented grant differs from the requested target;
2. a native authorization replay identity is already in an explicitly supplied
   consumed set; and
3. a denial still emits an effect through an undeclared synthetic surface.

An AEB evaluation record, native artifact, or CAID is not consumed by these
examples. The examples normalize selected facts into AECP's generic request and
grant vocabulary, then exercise AECP's own illustrative adapters and
decision-independent observer. The result is evidence about that mapping and
those local synthetic paths only.

## Concepts represented by the AECP profile

| AEB concept | AECP representation | Exact or approximate | Qualification and limit |
| --- | --- | --- | --- |
| Material-action mismatch at the final boundary | Equality between selected request fields and the same fields in a presented grant, exercised here through `grant.target` | Approximate | Exact for the selected AECP field, but not an AEB CAID evaluation. The example does not bind `order-1001`, `amount_minor`, or `currency` into the grant and does not show boundary recomputation after qualification. |
| Previously consumed native replay unit | Presented grant `nonce` compared with `request.context.seen_nonces` | Approximate | Tests refusal when consumed state is explicit input. It does not perform durable or atomic consumption, reservation, replica fencing, or state mutation between attempts. |
| Effect observation separate from the adapter decision | Adapter `decision` plus AECP `snapshot-diff-v1` observation | Exact within AECP; approximate as an AEB mapping | AECP independently derives persistent synthetic changes. It does not evaluate AEB's `VERIFIED`, `MATCH`, `SATISFIED`, `AUTHORIZED`, or execution-lifecycle states. |
| Alternate or equivalent effect path visible to the instrument | A subprocess emits `queue://alternate-settlement`, which was not a declared surface | Approximate | Demonstrates detection of one undeclared path that reaches AECP's synthetic effect port. It does not enumerate or mediate production bypass paths. |
| Matched qualification as a positive control | One fresh grant matches all six selected AECP binding fields and the declared synthetic settlement forms | Exact within AECP; approximate as an AEB mapping | Establishes non-vacuity for this local mapping. It is not evidence that the full AEB processing order ran. |

## Concepts not represented or deliberately deferred

The selected AECP profile does not test:

- construction and freezing of a complete AEB observed material action;
- native artifact signature, schema, issuer, audience, key-status,
  proof-of-possession, or native-policy verification;
- CAID derivation, complete material-field coverage, definition-source pins, or
  mapping-profile digests;
- field-origin assertions introduced in AEB `-04`, including snapshot,
  transformation, freshness, and status policy;
- AEC evidence-role satisfaction or separation of human, workload, policy, and
  qualification roles;
- the relying party's separate local authorization decision;
- durable atomic consumption, bounded reservation, replica fencing,
  `DISPATCH_PENDING`, or provider invocation;
- authoritative `EXECUTED`, `FAILED`, or `INDETERMINATE` classification; or
- authenticated reconciliation and the rule that reconciliation must not
  resurrect consumed authority.

The original Case 3 question remains a separate stateful follow-on: an effect
may have formed, the response was lost, and a blind retry must be refused until
authenticated reconciliation resolves the exact operation. AECP `v0.1-rc2`
creates a fresh adapter for each case and receives consumed state as input. It
therefore cannot establish durable multi-attempt custody or the AEB
`INDETERMINATE` lifecycle by these examples.

## Mapped inputs and observed results

All values below are inert local identifiers. Each run used a fresh synthetic
world with `ledger://settlements` as the only declared surface.

### Matched qualified positive control

Exact adapter input:

```json
{
  "request_token": "1111111111111111111111111111111111111111111111111111111111111111",
  "operation": "settle_order",
  "target": "merchant:beta",
  "consumer": "gateway:checkout",
  "use": "single_settlement",
  "subject": "agent:buyer",
  "origin": "workflow:checkout",
  "now": 100,
  "context": {
    "policy_epoch": 7,
    "seen_nonces": []
  },
  "grant_binding_fields": [
    "operation",
    "target",
    "consumer",
    "use",
    "subject",
    "origin"
  ],
  "presented_grants": [
    {
      "operation": "settle_order",
      "target": "merchant:beta",
      "consumer": "gateway:checkout",
      "use": "single_settlement",
      "subject": "agent:buyer",
      "origin": "workflow:checkout",
      "epoch": 7,
      "not_after": 120,
      "nonce": "native-authorization:order-1001"
    }
  ],
  "synthetic_effect": {
    "entries": [
      {
        "surface": "ledger://settlements",
        "key": "order-1001",
        "value": {
          "amount_minor": 2500,
          "currency": "USD",
          "recipient": "merchant:beta"
        }
      }
    ]
  }
}
```

Observed result:

```json
{
  "decision": "ALLOW",
  "decision_reason": "matching_fresh_grant",
  "observation": "FORMED",
  "verdict": "AS_EXPECTED",
  "divergence": "NONE",
  "declared_surface_changes": [
    {
      "surface": "ledger://settlements",
      "key": "order-1001",
      "change": "ADDED",
      "before_digest": null,
      "after_digest": "7a1a39a7447e3e9358603d8da91b7957620dfaa9220e9532e8cd3712b6bf1ae1"
    }
  ],
  "undeclared_surface_changes": []
}
```

This positive control establishes that the declared synthetic effect is
reachable when the selected AECP fields, epoch, validity window, and replay
precondition qualify. It does not establish any unmodeled AEB stage.

### Case 1: authorization for A presented for exact action B

Exact adapter input:

```json
{
  "request_token": "2222222222222222222222222222222222222222222222222222222222222222",
  "operation": "settle_order",
  "target": "merchant:beta",
  "consumer": "gateway:checkout",
  "use": "single_settlement",
  "subject": "agent:buyer",
  "origin": "workflow:checkout",
  "now": 100,
  "context": {
    "policy_epoch": 7,
    "seen_nonces": []
  },
  "grant_binding_fields": [
    "operation",
    "target",
    "consumer",
    "use",
    "subject",
    "origin"
  ],
  "presented_grants": [
    {
      "operation": "settle_order",
      "target": "merchant:alpha",
      "consumer": "gateway:checkout",
      "use": "single_settlement",
      "subject": "agent:buyer",
      "origin": "workflow:checkout",
      "epoch": 7,
      "not_after": 120,
      "nonce": "native-authorization:order-1001"
    }
  ],
  "synthetic_effect": {
    "entries": [
      {
        "surface": "ledger://settlements",
        "key": "order-1001",
        "value": {
          "amount_minor": 2500,
          "currency": "USD",
          "recipient": "merchant:beta"
        }
      }
    ]
  }
}
```

Observed result:

```json
{
  "decision": "DENY",
  "decision_reason": "no_matching_fresh_grant",
  "observation": "NOT_FORMED",
  "verdict": "AS_EXPECTED",
  "divergence": "NONE",
  "declared_surface_changes": [],
  "undeclared_surface_changes": []
}
```

The request targets `merchant:beta`; the presented grant targets
`merchant:alpha`. The current illustrative protected adapter rejects the
selected-field mismatch and the observer sees no persistent surface change.

This maps to AECP's existing `grant.target` control. In an AEB integration, a
complete boundary-owned material action and each action-bound artifact would
first have to be normalized and matched under a pinned CAID definition and
mapping profile. This example does not independently bind the settlement key,
amount, or currency and does not establish that a production boundary froze or
recomputed the action after qualification.

### Case 2: same native authorization under a fresh outer request

Exact adapter input:

```json
{
  "request_token": "3333333333333333333333333333333333333333333333333333333333333333",
  "operation": "settle_order",
  "target": "merchant:beta",
  "consumer": "gateway:checkout",
  "use": "single_settlement",
  "subject": "agent:buyer",
  "origin": "workflow:checkout",
  "now": 100,
  "context": {
    "policy_epoch": 7,
    "seen_nonces": [
      "native-authorization:order-1001"
    ]
  },
  "grant_binding_fields": [
    "operation",
    "target",
    "consumer",
    "use",
    "subject",
    "origin"
  ],
  "presented_grants": [
    {
      "operation": "settle_order",
      "target": "merchant:beta",
      "consumer": "gateway:checkout",
      "use": "single_settlement",
      "subject": "agent:buyer",
      "origin": "workflow:checkout",
      "epoch": 7,
      "not_after": 120,
      "nonce": "native-authorization:order-1001"
    }
  ],
  "synthetic_effect": {
    "entries": [
      {
        "surface": "ledger://settlements",
        "key": "order-1001",
        "value": {
          "amount_minor": 2500,
          "currency": "USD",
          "recipient": "merchant:beta"
        }
      }
    ]
  }
}
```

Observed result:

```json
{
  "decision": "DENY",
  "decision_reason": "no_matching_fresh_grant",
  "observation": "NOT_FORMED",
  "verdict": "AS_EXPECTED",
  "divergence": "NONE",
  "declared_surface_changes": [],
  "undeclared_surface_changes": []
}
```

The opaque outer `request_token` is fresh, while the presented grant's stable
native replay identity, `native-authorization:order-1001`, already appears in
`seen_nonces`. The current illustrative protected adapter compares the grant
nonce, not the outer request token, with that consumed set and refuses the
request.

The proposed mapping is:

- AECP `request_token`: fresh outer invocation or wrapper identity;
- AECP grant `nonce`: stable native-authorization replay unit; and
- AECP `request.context.seen_nonces`: replay units represented as already
  consumed.

This tests refusal given explicitly supplied consumed state. It does not show
that the replay unit was verified, consumed atomically, stored durably, shared
across replicas, reserved before dispatch, or kept closed through an uncertain
effect and reconciliation.

### Case 4: omitted equivalent effect path

Exact adapter input:

```json
{
  "request_token": "4444444444444444444444444444444444444444444444444444444444444444",
  "operation": "settle_order",
  "target": "merchant:beta",
  "consumer": "gateway:checkout",
  "use": "single_settlement",
  "subject": "agent:buyer",
  "origin": "workflow:checkout",
  "now": 100,
  "context": {
    "policy_epoch": 7,
    "seen_nonces": []
  },
  "grant_binding_fields": [
    "operation",
    "target",
    "consumer",
    "use",
    "subject",
    "origin"
  ],
  "presented_grants": [],
  "synthetic_effect": {
    "entries": [
      {
        "surface": "ledger://settlements",
        "key": "order-1001",
        "value": {
          "amount_minor": 2500,
          "currency": "USD",
          "recipient": "merchant:beta"
        }
      }
    ]
  }
}
```

The deliberately failing subprocess returned this validated response:

```json
{
  "decision": "DENY",
  "reason": "grant_missing",
  "emissions": [
    {
      "surface": "queue://alternate-settlement",
      "key": "order-1001",
      "value": {
        "amount_minor": 2500,
        "currency": "USD",
        "recipient": "merchant:beta"
      }
    }
  ]
}
```

Observed result:

```json
{
  "decision": "DENY",
  "decision_reason": "grant_missing",
  "observation": "FORMED",
  "verdict": "UNEXPECTED_FORMATION",
  "divergence": "DENIED_BUT_FORMED",
  "declared_surface_changes": [],
  "undeclared_surface_changes": [
    {
      "surface": "queue://alternate-settlement",
      "key": "order-1001",
      "change": "ADDED",
      "before_digest": null,
      "after_digest": "7a1a39a7447e3e9358603d8da91b7957620dfaa9220e9532e8cd3712b6bf1ae1"
    }
  ]
}
```

The declared settlement surface stayed unchanged, but the observer retained
and classified the dynamically named alternate surface. This is an instrument
counterexample, not a passing candidate-control fixture or a new stable
scenario. It demonstrates AECP detection when an alternate path is visible
through the synthetic effect port. It does not establish that all equivalent
production paths have been identified or placed behind an AEB boundary.

## Evidence ceiling and non-claims

For the two refusal mappings, the strongest supported statement is:

> No persistent change was observed on the declared or dynamically emitted
> synthetic surfaces between the sampled before and after snapshots.

For the alternate-path counterexample, the strongest supported statement is:

> One persistent addition on `queue://alternate-settlement` was observed and
> classified as undeclared even though the adapter returned `DENY`.

These runs do not establish that:

- no transient effect formed and was rolled back between snapshots;
- all semantically equivalent production paths were enumerated;
- a path outside the synthetic effect port was mediated;
- any production deployment implements AEB or complete mediation;
- any AEB native artifact was valid, current, action-matched, or sufficient;
- AECP implemented or tested the full AEB lifecycle; or
- AEB as a specification or any AEB implementation passed AECP.

## Validation record

The earlier issue review recorded the same three case outcomes at AECP commit
`6c38fc5c0595c598fac35cb835adbe7d813ec5a7`. On 2026-08-29, the exact inputs
above were re-run against current AECP source revision
`43832fa87213826036c6f0b0e4642c6084088565`:

| Entry | Adapter path | Decision / observation / verdict / divergence |
| --- | --- | --- |
| Positive control | `aecp.adapters.ProtectedAdapter` | `ALLOW / FORMED / AS_EXPECTED / NONE` |
| Case 1 | `aecp.adapters.ProtectedAdapter` | `DENY / NOT_FORMED / AS_EXPECTED / NONE` |
| Case 2 | `aecp.adapters.ProtectedAdapter` | `DENY / NOT_FORMED / AS_EXPECTED / NONE` |
| Case 4 | `aecp.adapters.SubprocessAdapter` plus `snapshot-diff-v1` | `DENY / FORMED / UNEXPECTED_FORMATION / DENIED_BUT_FORMED` |

The mapped-case rerun used the exact JSON printed in this note, a fresh
`SyntheticWorld(["ledger://settlements"])` per entry, and
`observe_surface_changes(before, after)`. Assertions checked every four-part
outcome above and the exact undeclared surface name. The run exited `0`.

No executable artifact or stable scenario is added by this mapping. The clean
repository validation command is:

```bash
./verify.sh
```

The clean run completed with exit status `0` on 2026-08-29:

```text
Ran 22 tests
OK
AECP CONFORMANCE_EXERCISE illustrative-protected: PASS
AECP-01 PASS failures=0
AECP-02 PASS failures=0
AECP-03 PASS failures=0
AECP-04 PASS failures=0
AECP-05 PASS failures=0
AECP-06 PASS failures=0
AECP-07 PASS failures=0
AECP SELF_TEST: PASS
validated scenarios=7 results=9
INDEX.json is current
```

## Provenance and attribution

- Public mapping proposal and maintainer disposition: [issue #1](https://github.com/visker83-del/aecp/issues/1)
- AEB source reviewed: `draft-schrock-action-evidence-boundary-04`, dated
  16 August 2026, with the source digest identified above
- Substantive mapping author: Iman Schrock, EMILIA Protocol, Inc.
- DCO sign-off for the substantive contribution:

```text
Signed-off-by: Iman Schrock <team@emiliaprotocol.ai>
```

This documentation contribution is made under the repository's CC BY 4.0
documentation license. Required repository attribution is:

> Agent Effect Control Profile (AECP), originally created by Certum Systems.

Technical citation, mapping, review, or later editorial cleanup does not imply
endorsement by AECP, Certum Systems, AEB, EMILIA Protocol, the IETF, or the
authors and maintainers of either project.
