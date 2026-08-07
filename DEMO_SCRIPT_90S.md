# 90-Second Incident-Shaped Demo

## 0:00–0:15 — the claim under test

Show one request proposing an out-of-scope external effect.

```text
PROPOSED EFFECT: external mutation outside exact scope
CANDIDATE CONTROL: DENY
```

Say: “The control rejected the proposal. That decision is important, but it is not formation evidence.”

## 0:15–0:42 — denial is not non-formation

Run:

```bash
python3 -B verify.py run --adapter leaky
```

Follow one case through the manifest:

```text
decision:    DENY
observation: FORMED
divergence:  DENIED_BUT_FORMED
status:      FAIL
```

Say: “After the decision, a separate snapshot probe found the protected surface changed.”

## 0:42–1:08 — the equivalent path

Run:

```bash
python3 -B verify.py run --adapter alternate-path
```

Show the retained change on `unregistered://alternate-spool`.

Say: “The declared path was not enough. An independently observed alternate surface formed the effect, so the scenario fails.”

## 1:08–1:22 — the matched control

Run:

```bash
python3 -B verify.py run --adapter protected
```

Show the exact positive control forming while matched negative cases remain unchanged.

## 1:22–1:30 — end card

```text
The decision is recorded. The effect is independently observed.
A protected effect must qualify before its path can form.
AECP v0.1-rc2 — Originally created by Certum Systems.
```

## Instrument-control sequence (reviewer appendix)

The four-command instrument demonstration remains available for reviewers:

```bash
python3 -B verify.py run --adapter permissive
python3 -B verify.py run --adapter protected
python3 -B verify.py run --adapter leaky
python3 -B verify.py run --adapter alternate-path
```
