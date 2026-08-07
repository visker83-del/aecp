# Contributing

We welcome safe, reproducible counterexamples, missing surfaces, adapter examples, and provenance corrections.

## Developer Certificate of Origin

Contributions use DCO 1.1 sign-off. Add this line to each commit:

```text
Signed-off-by: Your Name <your.email@example.com>
```

By signing off, you certify the contribution under `DCO.txt`. Inbound contributions are accepted under the same license that applies to the contributed material.

## Good counterexample format

Include:

1. scenario and case;
2. protected effect that remains possible;
3. alternate path or missing binding;
4. harmless local reproduction;
5. expected and observed manifest excerpt;
6. source/provenance for incident-derived claims.

Do not submit real credentials, live malicious payloads, attack instructions for real systems, personal information, or private incident transcripts.

## Mechanism boundary

Public discussion can identify a missing requirement or probe without requiring any vendor to disclose a proprietary implementation. A valid counterexample is not rejected because a maintainer declines to discuss private mechanisms.

## Review cadence

- issue intake: continuous;
- stable fixture review: at least quarterly;
- critical specification corrections: as needed.

Run before submitting:

```bash
./verify.sh
python3 -m unittest discover -s tests -v
python3 tools/make_index.py --check
```
