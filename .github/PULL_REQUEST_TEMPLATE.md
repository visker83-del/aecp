## Summary

Describe the change and why it belongs in AECP.

Related issue: <!-- e.g. #1 -->

## Change type

- [ ] Code or tooling
- [ ] Normative profile or stable scenario
- [ ] Non-normative interoperability mapping
- [ ] Documentation or provenance correction
- [ ] Generated result or index update

## Scope and claim boundary

- [ ] The change stays within AECP's declared adapter and observation profile.
- [ ] New claims identify what was observed, what was not observed, and any important evidence ceiling.
- [ ] A non-normative mapping does not make the external mechanism an AECP dependency, endorsement, certification, or proof of production deployment.

## License and provenance

- [ ] I checked `LICENSE.md` and identified the license that applies to every changed file.
- [ ] I wrote the contributed material or otherwise have the right to submit it under the applicable AECP license.
- [ ] External specifications, incidents, fixtures, quotations, and prior work are identified with versioned sources where practical.
- [ ] I have not included credentials, personal information, private incident material, or live malicious payloads.

Applicable license(s): <!-- BSD-3-Clause, CC-BY-4.0, or explain -->

Provenance and versioned sources: <!-- links, revisions, issue references -->

Fixture hash: <!-- content_sha256 if this PR adds or changes a fixture; otherwise n/a -->

## DCO

- [ ] Every commit in this pull request includes my `Signed-off-by:` line and complies with `DCO.txt`.

The checkbox is a review aid, not a substitute for commit sign-off.

## Validation

List the commands run and their results. For changes that can affect verification, run:

```text
python -m unittest discover -s tests -v
python -B verify.py selftest
python -B tools/validate_all.py
python tools/make_index.py --check
```

Validation result:

<!-- Include any intentionally deferred checks. -->
