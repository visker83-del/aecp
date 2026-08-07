# Security Policy

## Bundled safety boundary

Bundled fixtures and adapters are local and synthetic. They do not contact public services, people, accounts, or networks and contain no real credentials or malicious payloads.

## External adapter warning

AECP does not sandbox third-party adapters. A Python adapter executes inside the harness process; an adapter command executes as a local subprocess. Review the adapter and use an isolated environment appropriate to its risk.

Loading a `module:factory` imports the named Python module and executes its top-level code before the factory can be inspected. Treat both the module and factory as executable code.

Do not run adapters from untrusted pull requests with repository secrets or privileged credentials.

## Reporting

For vulnerabilities in the harness, use a private GitHub security advisory when available or contact the repository maintainers through the security contact listed in the public repository profile. Do not include live credentials or weaponized payloads.

Public fixture mistakes and harmless counterexamples may be reported as ordinary issues.
