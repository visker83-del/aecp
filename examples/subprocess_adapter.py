#!/usr/bin/env python3
"""A copyable subprocess adapter showing how to wrap an external control.

The point of this file is the wiring, not the control. `ExampleCandidate`
stands in for the system you actually want to exercise. Replace it with a call
into your control and keep the adapter half unchanged.

The adapter never looks at the returned decision to decide what to emit. It
forwards whatever the candidate's actuation path attempted. That separation is
what lets AECP observe a denial that still formed an effect; an adapter that
emits because the decision said ALLOW can never produce that observation and
tells you nothing about the effect path.

Run the conformance exercise:

    python3 -B verify.py run \\
      --adapter-label example-subprocess \\
      --adapter-command python3 examples/subprocess_adapter.py

Check your own wiring (see examples/README.md):

    AECP_EXAMPLE_FAULT=leak-after-deny python3 -B verify.py run \\
      --adapter-label example-subprocess-fault \\
      --adapter-command python3 examples/subprocess_adapter.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Mapping


class ExampleCandidate:
    """Stand-in for the control under test.

    A real candidate has two things AECP needs kept apart: a decision, and an
    actuation path that attempts effects. Here `run` returns the decision and
    reports each attempted effect through `on_effect`. In your integration
    `on_effect` is whatever hook, callback, or interceptor your control already
    uses when it is about to write, send, or otherwise act.

    If your control has no way to surface an attempted effect independently of
    its decision, AECP cannot evaluate effect-path non-formation for that
    integration. Say so rather than reporting a pass.
    """

    def __init__(self, fault: str | None = None) -> None:
        self._fault = fault

    def _decide(self, request: Mapping[str, Any]) -> tuple[str, str]:
        context = request.get("context", {})
        if not self._has_matching_grant(request):
            return "DENY", "no_qualifying_grant"

        # Two operations carry an extra qualification dimension. A real
        # integration maps these onto whatever its own control calls them.
        operation = request.get("operation")

        if operation == "artifact_reentry":
            if context.get("origin_qualified") is not True:
                return "DENY", "origin_not_qualified"

        if operation == "admit_derived_state":
            parent = set(context.get("parent_authorities", []))
            derived = set(context.get("derived_authorities", []))
            if not derived.issubset(parent):
                return "DENY", "derived_authority_amplified"

        return "ALLOW", "qualified"

    def _has_matching_grant(self, request: Mapping[str, Any]) -> bool:
        binding = request.get("grant_binding_fields", [])
        context = request.get("context", {})
        seen = set(context.get("seen_nonces", []))
        epoch = context.get("policy_epoch")
        now = request.get("now")
        for grant in request.get("presented_grants", []):
            if any(grant.get(field) != request.get(field) for field in binding):
                continue
            if grant.get("epoch") != epoch:
                continue
            if grant.get("not_after") is not None and now > grant["not_after"]:
                continue
            if grant.get("nonce") in seen:
                continue
            return True
        return False

    def run(
        self,
        request: Mapping[str, Any],
        on_effect: Callable[[Mapping[str, Any]], None],
    ) -> tuple[str, str]:
        decision, reason = self._decide(request)
        # The actuation path. A correctly behaving control acts only when it
        # qualified the request; the fault mode below is a deliberately broken
        # control used to prove your wiring reaches this path at all.
        act = decision == "ALLOW" or self._fault == "leak-after-deny"
        if act:
            for entry in request.get("synthetic_effect", {}).get("entries", []):
                on_effect(entry)
        return decision, reason


def handle(request: Mapping[str, Any]) -> dict[str, Any]:
    attempted: list[Mapping[str, Any]] = []
    candidate = ExampleCandidate(fault=os.environ.get("AECP_EXAMPLE_FAULT"))

    decision, reason = candidate.run(request, on_effect=attempted.append)

    # Emissions come from what the candidate attempted, never from `decision`.
    emissions = [
        {"surface": entry["surface"], "key": entry["key"], "value": entry["value"]}
        for entry in attempted
    ]
    return {"decision": decision, "reason": reason, "emissions": emissions}


def main() -> int:
    line = sys.stdin.readline()
    if not line.strip():
        print("empty request on stdin", file=sys.stderr)
        return 1
    try:
        request = json.loads(line)
    except json.JSONDecodeError as exc:
        print(f"malformed request: {exc}", file=sys.stderr)
        return 1

    response = handle(request)
    sys.stdout.write(json.dumps(response, separators=(",", ":"), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
