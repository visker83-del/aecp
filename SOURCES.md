# Sources

## Primary incident source
- UK AI Security Institute, *Incident Report: unsanctioned agent behaviour during cyber testing*, 4 August 2026.
  - https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing
- UK AI Security Institute, public technical report `INC-2026-07-28-01`.
  - Official public locator used by AECP: https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing
  - Fixture section locators refer to the long-form report associated with that official incident page. AECP does not bundle a copy; AECP-03, AECP-04, and AECP-07 are explicitly `ANALOGOUS`, not `DIRECT`.

## Cross-lab context and source roadmap — non-normative

These sources motivate future incident-shaped work. They do not change the seven v0.1 classes or their AISI provenance.

- OpenAI, *OpenAI and Hugging Face partner to address security incident during model evaluation*, 21 July 2026.
  - https://openai.com/index/hugging-face-model-evaluation-security-incident/
  - Official account of vulnerabilities chained across an OpenAI research environment and Hugging Face production infrastructure.
- Hugging Face, *Security incident disclosure — July 2026*, 16 July 2026.
  - https://huggingface.co/blog/security-incident-july-2026
- Hugging Face, *Anatomy of a Frontier Lab Agent Intrusion: A Technical Timeline of the July 2026 Incident*, 27 July 2026.
  - https://huggingface.co/blog/agent-intrusion-technical-timeline
  - Official forensic reconstruction relevant to multi-stage execution and campaign continuity across short-lived environments.
- Anthropic, *Investigating three real-world incidents in our cybersecurity evaluations*, 30 July 2026.
  - https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals
  - Official account of three incidents in which models reached real organizations from misconfigured third-party evaluation environments.
- OpenAI, *Third-party cyber evaluations involving OpenAI models*, 4 August 2026.
  - https://openai.com/index/third-party-cyber-evaluations-involving-openai-models/
  - Official account of separate UK AISI and Irregular evaluation-boundary incidents.
- Anthropic, *Mapping AI-enabled cyber threats: Insights from the LLM ATT&CK Navigator*, 3 June 2026.
  - https://www.anthropic.com/research/attack-navigator
  - Official threat-intelligence context for multi-step autonomous execution and AI-directed pivot decisions.
- OpenAI, *GPT-5.6 System Card*, 9 July 2026, including external evaluations by Irregular and UK AISI.
  - https://deploymentsafety.openai.com/gpt-5-6
  - Capability-evaluation context only; not treated as an AECP incident source.

### Independent investigation of the same incident

- METR / Redwood Research, independent investigation of the OpenAI/Hugging Face incident, 26 August 2026.
  - https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/
  - Supersedes the earlier presentation- and reporting-derived status of the message-board and artifact-mediated cross-run coordination details, which had been held pending a stable technical publication. Records shared-board coordination across agents intended to be isolated, and spoofed tool calls in agent transcripts.
  - Still not used as normative fixture provenance in v0.1. The seven classes remain AISI-derived.

## Constructed scenarios — not incidents

Deliberately built to elicit a behavior. Their authors say so. Rates and model rankings from these do not transfer to deployment.

- Anthropic Alignment Science, *agentic misalignment*, summer 2026.
  - https://alignment.anthropic.com/2026/agentic-misalignment-summer-2026/
  - Covert sabotage, record tampering, judges changing labels on anticipated training consequences, and human-proxy coaching. The authors state these "are not real-world incidents" and caution that the search was aimed at finding failures.

## Prospective assessments — not observations

- METR, frontier risk report, 19 May 2026.
  - https://metr.org/blog/2026-05-19-frontier-risk-report/
  - Assessment from February–March 2026 evaluations. Concludes internally deployed agents "plausibly had the means, motive, and opportunity to start small rogue deployments, but they did not have the means to make them highly robust." A capability judgment, not a report that a rogue deployment occurred.

## Related authorization/evidence work
- `draft-nivalto-agentroa-route-authorization-01`, *Agent Route Origin Authorization (AgentROA): A Cryptographic Policy Enforcement Framework for AI Agent Actions*, 16 April 2026.
  - https://datatracker.ietf.org/doc/draft-nivalto-agentroa-route-authorization/01/
- `draft-lee-orprg-permit-receipts-00`, *Permit Receipts for Permit-Before-Commit Authorization of AI-Agent and Workload External Effects*, 4 June 2026.
  - https://datatracker.ietf.org/doc/draft-lee-orprg-permit-receipts/00/
- `draft-rampalli-scitt-capsule-provenance-binding-00`, *Binding Per-Action Authorization and Memory Provenance into Agent Action Capsules*, 5 July 2026.
  - https://www.ietf.org/archive/id/draft-rampalli-scitt-capsule-provenance-binding-00.html
- `draft-schrock-action-evidence-boundary`, *The Action Evidence Boundary for Consequential Agent Effects*.
  - first revision `-00`: 21 July 2026
  - Datatracker revision observed during 7 August 2026 package review: `-03`, dated 3 August 2026
  - Current revision: `-04`, dated 16 August 2026
  - https://datatracker.ietf.org/doc/draft-schrock-action-evidence-boundary/

Internet-Drafts are works in progress and are not IETF-endorsed standards merely by being published.
