# Non-Normative Interoperability Mappings

This directory holds version-pinned explanations of how an external mechanism can be represented within AECP's declared adapter and observation profile.

These documents are non-normative. They do not add a stable AECP scenario, make an external specification an AECP dependency, certify an implementation, prove production deployment, or imply endorsement by either project.

## Admission requirements

Each mapping should:

1. identify the exact external specification or implementation revision;
2. identify the AECP profile and release against which the mapping was checked;
3. distinguish concepts represented exactly, represented approximately, and not represented;
4. include a matched qualified positive control where applicable;
5. state expected decision and independently observed effect outcomes;
6. preserve AECP's evidence ceiling and list material non-claims;
7. record authorship, provenance, and the public discussion that led to the mapping; and
8. enter through a DCO-signed commit under the license identified by `LICENSE.md`.

Mappings are reviewed on technical fit and reproducibility. Maintainers may edit presentation after the substantive contributor's signed-off commit, without changing technical meaning or authorship.

## File naming and updates

Use a short external-mechanism name plus a pinned revision, for example `aeb-04.md`. A later external revision should receive a new review and either a new file or an explicit revision update with its validation record.

If a mapping exposes coverage that the current AECP profile cannot express, record that gap separately. Do not silently convert the mapping into a normative scenario.
