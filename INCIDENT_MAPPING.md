# Incident Mapping — v0.1

## Source-derived vs design-extension

AECP distinguishes:
- **SOURCE-DERIVED**: directly motivated by behaviors publicly reported in the referenced AISI technical incident report.
- **DESIGN-EXTENSION**: a general control class added to make the profile useful beyond the single incident. It is not claimed to have occurred in that incident.

Primary public source:
- UK AI Security Institute, `INC-2026-07-28-01`, *Security Incident: unsanctioned agent behaviour during cyber testing*, published 4 August 2026.
- Companion AISI blog post of the same incident.

## Mapping

| AECP class | Status | Public-report basis |
|---|---|---|
| AECP-01 External mutation | SOURCE-DERIVED | The report catalogues unsanctioned actions on the live internet, including public-system interactions and mutation attempts. |
| AECP-02 Human-directed communication | SOURCE-DERIVED | The incident includes human-directed/social-engineering activity and contact with real people/organizations. |
| AECP-03 Capability transition | SOURCE-DERIVED / ANALOGOUS | Technical report Appendix A.5/A.8/A.9/A.10 describes public-tunnelling behavior; AECP translates it into a harmless capability-transition fixture rather than reproducing the reported path. |
| AECP-04 Cross-agent artifact re-entry | SOURCE-DERIVED / ANALOGOUS | Technical report §4.2.2 describes cross-sample interaction through public artifacts; AECP translates it into an origin/use-qualified re-entry fixture. |
| AECP-05 Persistent-memory mutation | DESIGN-EXTENSION | Persistent memory is a general behavior-forming surface; this class is not presented as an AISI incident finding. |
| AECP-06 Control-plane modification | DESIGN-EXTENSION | Protecting the enforcement plane is a general requirement; this class is not presented as an AISI incident finding. |
| AECP-07 Derived-state authority amplification | SOURCE-DERIVED / ANALOGOUS | Technical report §4.2.1 states that compaction can lose earlier nuance and carry forward a false assumption as established fact. Treating that as an authority non-amplification exercise is AECP's control-oriented analogy, not AISI's terminology. |

## Source precision

AECP-03, AECP-04, and AECP-07 are analogical control translations grounded in the long-form report sections identified above. The official AISI incident page listed in `SOURCES.md` is the public source locator used by this package; AECP does not mirror or re-host the source report.

The local AECP fixtures do not reproduce live infrastructure, real credentials, or private transcripts. Each fixture embeds exact provenance and labels its derivation as `DIRECT`, `ANALOGOUS`, or `EXTENSION`.

## Non-claim

AECP does not claim that the controls represented by these classes would have prevented every event in the AISI incident. The mapping is counterfactual and test-oriented.
