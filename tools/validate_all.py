#!/usr/bin/env python3
"""Validate every published scenario and result with the normative RC2 validator."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aecp.canonical import canonical_sha256, file_sha256, strict_json_loads  # noqa: E402
from aecp.runner import SCOPE_NOTE  # noqa: E402
from aecp.schema import validate_manifest, validate_scenario  # noqa: E402


def main() -> int:
    scenario_paths = sorted((ROOT / "scenarios").glob("aecp-*.json"))
    result_paths = sorted((ROOT / "results").glob("*.json"))
    if not scenario_paths or not result_paths:
        raise ValueError("published scenarios and results must both be present")
    scenario_values = {}
    scenario_files = {}
    for path in scenario_paths:
        scenario = strict_json_loads(path.read_text(encoding="utf-8"))
        validate_scenario(scenario)
        scenario_values[scenario["id"]] = scenario
        scenario_files[scenario["id"]] = path
    for path in result_paths:
        manifest = strict_json_loads(path.read_text(encoding="utf-8"))
        validate_manifest(manifest)
        if manifest["content"]["scope_note"] != SCOPE_NOTE:
            raise ValueError(f"{path.name}: non-canonical scope note")
        records = manifest["content"]["scenarios"]
        if [record["scenario_id"] for record in records] != list(scenario_values):
            raise ValueError(f"{path.name}: scenario set/order does not match published fixtures")
        for record in records:
            fixture = ROOT / record["fixture_path"]
            scenario = strict_json_loads(fixture.read_text(encoding="utf-8"))
            expected_path = scenario_files[scenario["id"]]
            if fixture != expected_path:
                raise ValueError(f"{path.name}: non-canonical fixture path for {scenario['id']}")
            if record["scenario_id"] != scenario["id"]:
                raise ValueError(f"{path.name}: scenario ID does not match {fixture}")
            expected_fields = {
                "scenario_name": scenario["name"],
                "source_status": scenario["source_status"],
                "protected_surfaces": [item["id"] for item in scenario["protected_surfaces"]],
                "probe_contract": "snapshot-diff-v1",
                "trust_assumptions": scenario["trust_assumptions"],
                "untested_paths": scenario["untested_paths"],
            }
            for field, expected in expected_fields.items():
                if record[field] != expected:
                    raise ValueError(f"{path.name}: {field} does not match {fixture.name}")
            fixture_cases = [scenario["positive_control"], *scenario["negative_cases"]]
            result_cases = record["cases"]
            if len(result_cases) != len(fixture_cases):
                raise ValueError(f"{path.name}: case count does not match {fixture.name}")
            for index, (result_case, fixture_case) in enumerate(zip(result_cases, fixture_cases)):
                expected_kind = "POSITIVE_CONTROL" if index == 0 else "NEGATIVE"
                if result_case["case_id"] != fixture_case["id"]:
                    raise ValueError(f"{path.name}: case ID/order does not match {fixture.name}")
                if result_case["kind"] != expected_kind or result_case["expected"] != fixture_case["expect"]:
                    raise ValueError(f"{path.name}: case semantics do not match {fixture.name}")
            if record["fixture_file_sha256"] != file_sha256(fixture):
                raise ValueError(f"{path.name}: stale fixture byte digest for {fixture.name}")
            if record["fixture_canonical_sha256"] != canonical_sha256(scenario):
                raise ValueError(f"{path.name}: stale fixture canonical digest for {fixture.name}")
    print(f"validated scenarios={len(scenario_paths)} results={len(result_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
