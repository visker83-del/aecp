"""AECP scenario runner with decision-independent synthetic surface observation."""

from __future__ import annotations

import copy
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Mapping

from .adapters import Adapter
from .canonical import canonical_sha256, file_sha256, strict_json_loads
from .schema import validate_manifest, validate_scenario
from .world import SyntheticWorld, observe_surface_changes


PROFILE_VERSION = "0.1-rc2"
SCOPE_NOTE = (
    "This result exercises one named adapter against local synthetic fixtures and snapshot-diff probes. "
    "It is not production certification and does not establish complete mediation of a deployment."
)


def load_scenarios(directory: Path) -> list[tuple[Path, dict[str, Any]]]:
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob("aecp-*.json")):
        value = strict_json_loads(path.read_text(encoding="utf-8"))
        validate_scenario(value)
        loaded.append((path, value))
    if not loaded:
        raise ValueError(f"no scenarios found in {directory}")
    return loaded


def known_surface_universe(scenarios: list[tuple[Path, Mapping[str, Any]]]) -> tuple[str, ...]:
    surfaces: set[str] = set()
    for _, scenario in scenarios:
        surfaces.update(item["id"] for item in scenario["protected_surfaces"])
    return tuple(sorted(surfaces))


def _request_for(scenario: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(case["request"])
    request.update(
        {
            # Do not disclose human-readable oracle labels such as
            # "wrong-target" to the adapter under exercise.
            "request_token": canonical_sha256(
                {"scenario_id": scenario["id"], "case_id": case["id"]}
            ),
            "grant_binding_fields": list(scenario["grant_binding_fields"]),
            "presented_grants": copy.deepcopy(case["grants"]),
            "synthetic_effect": copy.deepcopy(scenario["synthetic_effect"]),
        }
    )
    return request


def _run_case(
    scenario: Mapping[str, Any],
    case: Mapping[str, Any],
    kind: str,
    adapter_factory: Callable[[], Adapter],
    all_surfaces: tuple[str, ...],
) -> dict[str, Any]:
    world = SyntheticWorld(all_surfaces)
    before = world.snapshot()
    decision = "ERROR"
    decision_reason = "adapter_not_run"
    error: str | None = None
    error_observation = "ERROR"
    try:
        adapter = adapter_factory()
        response = adapter.handle(_request_for(scenario, case), world.port())
        if not isinstance(response, Mapping):
            raise ValueError("adapter response must be a mapping")
        decision = response.get("decision", "ERROR")
        decision_reason = response.get("reason", "unspecified")
        if decision not in {"ALLOW", "DENY", "ERROR"}:
            raise ValueError(f"invalid adapter decision: {decision}")
        if not isinstance(decision_reason, str) or not decision_reason:
            raise ValueError("adapter reason must be a non-empty string")
    except Exception as exc:  # an adapter failure is inconclusive, never evidence of absence
        decision = "ERROR"
        decision_reason = "adapter_exception"
        error = f"{type(exc).__name__}: {exc}"
        if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
            error_observation = "TIMEOUT"
    try:
        after = world.snapshot()
    except Exception as exc:
        # Defensive boundary for an in-process adapter that bypasses the public
        # port and corrupts private simulator state. No absence claim is made.
        decision = "ERROR"
        decision_reason = "snapshot_exception"
        snapshot_error = f"{type(exc).__name__}: {exc}"
        error = f"{error}; {snapshot_error}" if error else snapshot_error
        error_observation = "ERROR"
        after = before

    # Deliberately accepts snapshots only. Adapter decision is not an input to observation.
    changes = observe_surface_changes(before, after)
    declared = {item["id"] for item in scenario["protected_surfaces"]}
    declared_changes = [asdict(change) for change in changes if change.surface in declared]
    undeclared_changes = [asdict(change) for change in changes if change.surface not in declared]
    changed_declared_surfaces = {change["surface"] for change in declared_changes}

    probes = []
    for surface in scenario["protected_surfaces"]:
        probes.append(
            {
                "surface": surface["id"],
                "probe": surface["probe"],
                "observed": "PRESENT" if surface["id"] in changed_declared_surfaces else "ABSENT",
            }
        )

    if error is not None or decision == "ERROR":
        observation = error_observation
        if changes:
            # An adapter failure cannot erase effects that the independent
            # observer already saw.  Observed formation dominates uncertainty.
            verdict = "UNEXPECTED_FORMATION"
        else:
            verdict = "INCONCLUSIVE"
    else:
        any_change = bool(changes)
        observation = "FORMED" if any_change else "NOT_FORMED"
        all_declared_changed = changed_declared_surfaces == declared
        if case["expect"] == "NON_FORMED":
            verdict = "AS_EXPECTED" if not any_change else "UNEXPECTED_FORMATION"
        elif undeclared_changes:
            verdict = "UNEXPECTED_FORMATION"
        elif all_declared_changed:
            verdict = "AS_EXPECTED"
        elif not declared_changes:
            verdict = "UNEXPECTED_NON_FORMATION"
        else:
            verdict = "UNEXPECTED_PARTIAL_FORMATION"

    if decision == "ERROR" and changes:
        divergence = "FORMED_DURING_ERROR"
    elif decision == "DENY" and observation == "FORMED":
        divergence = "DENIED_BUT_FORMED"
    elif decision == "ALLOW" and observation == "NOT_FORMED":
        divergence = "ALLOWED_BUT_NOT_FORMED"
    else:
        divergence = "NONE"

    return {
        "case_id": case["id"],
        "kind": kind,
        "expected": case["expect"],
        "decision": decision,
        "decision_reason": decision_reason,
        "observation": observation,
        "verdict": verdict,
        "divergence": divergence,
        "declared_surface_changes": declared_changes,
        "undeclared_surface_changes": undeclared_changes,
        "probes": probes,
        "error": error,
    }


def _scenario_status(cases: list[Mapping[str, Any]]) -> str:
    if any(
        case["verdict"] not in {"AS_EXPECTED", "INCONCLUSIVE"}
        or case["divergence"] != "NONE"
        for case in cases
    ):
        return "FAIL"
    if any(case["verdict"] == "INCONCLUSIVE" for case in cases):
        return "INCONCLUSIVE"
    return "PASS"


def run_suite(
    scenario_dir: Path,
    adapter_factory: Callable[[], Adapter],
    *,
    run_type: str,
) -> dict[str, Any]:
    scenarios = load_scenarios(scenario_dir)
    all_surfaces = known_surface_universe(scenarios)
    try:
        adapter_info = dict(adapter_factory().describe())
    except Exception as exc:
        raise ValueError(f"adapter setup/describe failed: {type(exc).__name__}: {exc}") from exc
    records = []

    for path, scenario in scenarios:
        cases = [
            _run_case(scenario, scenario["positive_control"], "POSITIVE_CONTROL", adapter_factory, all_surfaces)
        ]
        cases.extend(
            _run_case(scenario, case, "NEGATIVE", adapter_factory, all_surfaces)
            for case in scenario["negative_cases"]
        )
        status = _scenario_status(cases)
        records.append(
            {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "source_status": scenario["source_status"],
                "fixture_path": f"scenarios/{path.name}",
                "fixture_file_sha256": file_sha256(path),
                "fixture_canonical_sha256": canonical_sha256(scenario),
                "protected_surfaces": [item["id"] for item in scenario["protected_surfaces"]],
                "probe_contract": "snapshot-diff-v1",
                "trust_assumptions": scenario["trust_assumptions"],
                "untested_paths": scenario["untested_paths"],
                "evidence_tier": "PARTIAL" if status == "INCONCLUSIVE" else "EXERCISED",
                "status": status,
                "cases": cases,
            }
        )

    statuses = {record["status"] for record in records}
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "INCONCLUSIVE" in statuses:
        overall = "INCONCLUSIVE"
    else:
        overall = "PASS"

    content = {
        "profile_version": PROFILE_VERSION,
        "run_type": run_type,
        "implementation": adapter_info,
        "scope_note": SCOPE_NOTE,
        "overall": overall,
        "scenarios": records,
    }
    manifest = {
        "manifest_version": "1.0",
        "content_sha256": canonical_sha256(content),
        "content": content,
    }
    validate_manifest(manifest)
    return manifest
