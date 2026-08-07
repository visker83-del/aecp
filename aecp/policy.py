"""Generic example qualification logic used only by the protected toy adapter."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def _get_path(value: Mapping[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _matching_grant(request: Mapping[str, Any]) -> tuple[bool, str]:
    now = request.get("now")
    context = request.get("context", {})
    seen_nonces = set(context.get("seen_nonces", []))
    policy_epoch = context.get("policy_epoch")
    bindings: Sequence[str] = request.get("grant_binding_fields", [])
    for grant in request.get("presented_grants", []):
        if any(_get_path(grant, field) != _get_path(request, field) for field in bindings):
            continue
        if not isinstance(now, int) or grant.get("not_after", -1) < now:
            continue
        if grant.get("epoch") != policy_epoch:
            continue
        if grant.get("nonce") in seen_nonces:
            continue
        return True, "matching_fresh_grant"
    return False, "no_matching_fresh_grant"


def qualifies(request: Mapping[str, Any]) -> tuple[bool, str]:
    context = request.get("context", {})
    operation = request.get("operation")

    allowed, reason = _matching_grant(request)
    if not allowed:
        return False, reason

    if operation == "artifact_reentry" and context.get("origin_qualified") is not True:
        return False, "origin_not_qualified"

    if operation == "admit_derived_state":
        parent = set(context.get("parent_authorities", []))
        derived = set(context.get("derived_authorities", []))
        if not derived.issubset(parent):
            return False, "derived_authority_amplified"
        return True, "matching_grant_and_nonamplifying_derivation"

    return True, reason
