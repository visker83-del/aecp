# Related Work — Authorization/Evidence Cluster

AECP is positioned as a **test and conformance profile**, not as a competing wire protocol.

The following 2026 individual Internet-Drafts are particularly relevant:

1. **Agent Route Origin Authorization (AgentROA)**  
   `draft-nivalto-agentroa-route-authorization-01` — 16 April 2026.  
   Cryptographic action scope, delegation, per-hop attestation, and execution receipts.

2. **Permit Receipts for Permit-Before-Commit Authorization of AI-Agent and Workload External Effects**  
   `draft-lee-orprg-permit-receipts-00` — 4 June 2026.  
   Canonical effect request, action digest, policy epoch, scope, revocation/recency and anti-replay checks before effect commitment.

3. **Binding Per-Action Authorization and Memory Provenance into Agent Action Capsules**  
   `draft-rampalli-scitt-capsule-provenance-binding-00` — 5 July 2026.  
   Binds per-action authorization references and memory-provenance references into an agent action capsule; explicitly includes a defensive-publication notice.

4. **The Action Evidence Boundary for Consequential Agent Effects**  
   `draft-schrock-action-evidence-boundary` — first revision `-00` published 21 July 2026; current Datatracker revision observed: `-04`, dated 16 August 2026.  
   Executor-side processing model for joining authorization/evidence to exact effects, local authorization, durable consumption/reservation, dispatch lifecycle, effect outcomes, and reconciliation.  
   - https://datatracker.ietf.org/doc/draft-schrock-action-evidence-boundary/

These are individual Internet-Drafts, not IETF-endorsed standards.

## AECP's relationship

Those drafts primarily propose authorization/evidence models and processing structures.

AECP asks a different operational question:

> Given any chosen authorization/evidence/control mechanism, can an incident-derived protected effect path still form when the declared qualification condition is absent?

AECP therefore aims to be usable against:
- an IETF-derived mechanism;
- a cloud-vendor control;
- an internal lab control;
- a research prototype;
- a Certum implementation.

No relationship or endorsement by the IETF or the listed authors is implied.
