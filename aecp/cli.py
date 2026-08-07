"""Command-line interface for AECP local exercises."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .adapters import BUILTINS, SubprocessAdapter, load_adapter
from .canonical import canonical_sha256, strict_json_loads, write_json
from .runner import run_suite
from .schema import SchemaError, validate_manifest, validate_scenario
from .world import observe_surface_changes


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
RESULTS = ROOT / "results"


def _print_summary(manifest: Mapping[str, Any]) -> None:
    content = manifest["content"]
    print(f"AECP {content['run_type']} {content['implementation']['id']}: {content['overall']}")
    for scenario in content["scenarios"]:
        failures = sum(
            case["verdict"] != "AS_EXPECTED" or case["divergence"] != "NONE"
            for case in scenario["cases"]
        )
        print(f"{scenario['scenario_id']} {scenario['status']} failures={failures}")
        notable = [
            case for case in scenario["cases"]
            if case["divergence"] != "NONE" or case["undeclared_surface_changes"]
        ]
        for case in notable[:3]:
            undeclared = sorted({item["surface"] for item in case["undeclared_surface_changes"]})
            suffix = f" undeclared={undeclared}" if undeclared else ""
            print(f"  {case['case_id']}: divergence={case['divergence']}{suffix}")
    print(content["scope_note"])


def _run(args: argparse.Namespace) -> int:
    if args.adapter_command:
        command = tuple(args.adapter_command)
        factory = lambda: SubprocessAdapter(command, label=args.adapter_label)
    else:
        factory = load_adapter(args.adapter)
    manifest = run_suite(SCENARIOS, factory, run_type=args.run_type)
    if args.output:
        write_json(Path(args.output), manifest)
    _print_summary(manifest)
    overall = manifest["content"]["overall"]
    return 0 if overall == "PASS" else 1


def _cell(manifest: Mapping[str, Any]) -> set[tuple[str, str]]:
    cells: set[tuple[str, str]] = set()
    for scenario in manifest["content"]["scenarios"]:
        for case in scenario["cases"]:
            if case["observation"] in {"FORMED", "NOT_FORMED"}:
                cells.add((case["decision"], case["observation"]))
    return cells


def evaluate_selftest(manifests: Mapping[str, Mapping[str, Any]], expected: Mapping[str, str]) -> list[str]:
    problems: list[str] = []
    for name, expected_overall in expected.items():
        observed = manifests[name]["content"]["overall"]
        if observed != expected_overall:
            problems.append(f"{name}: expected overall {expected_overall}, observed {observed}")

    for scenario in manifests["permissive"]["content"]["scenarios"]:
        for case in scenario["cases"]:
            if case["kind"] == "NEGATIVE" and case["observation"] != "FORMED":
                problems.append(f"fixture reachability failure: {scenario['scenario_id']}:{case['case_id']}")

    cells: set[tuple[str, str]] = set()
    for manifest in manifests.values():
        cells.update(_cell(manifest))
    required_cells = {
        ("ALLOW", "FORMED"),
        ("ALLOW", "NOT_FORMED"),
        ("DENY", "FORMED"),
        ("DENY", "NOT_FORMED"),
    }
    if not required_cells.issubset(cells):
        problems.append(f"decision/effect cells missing: {sorted(required_cells - cells)}")

    signature = tuple(inspect.signature(observe_surface_changes).parameters)
    if signature != ("before", "after"):
        problems.append(f"observer accepts unexpected inputs: {signature}")

    leaky_divergences = {
        case["divergence"]
        for scenario in manifests["leaky"]["content"]["scenarios"]
        for case in scenario["cases"]
    }
    noop_divergences = {
        case["divergence"]
        for scenario in manifests["noop"]["content"]["scenarios"]
        for case in scenario["cases"]
    }
    if "DENIED_BUT_FORMED" not in leaky_divergences:
        problems.append("leaky adapter was not detected as DENIED_BUT_FORMED")
    if "ALLOWED_BUT_NOT_FORMED" not in noop_divergences:
        problems.append("noop adapter was not detected as ALLOWED_BUT_NOT_FORMED")

    alternate_changes = [
        case["undeclared_surface_changes"]
        for scenario in manifests["alternate-path"]["content"]["scenarios"]
        for case in scenario["cases"]
    ]
    if not any(alternate_changes):
        problems.append("undeclared alternate surface was not detected")
    return problems


def _selftest(_: argparse.Namespace) -> int:
    RESULTS.mkdir(exist_ok=True)
    expected = {
        "protected": "PASS",
        "permissive": "FAIL",
        "leaky": "FAIL",
        "deadend": "FAIL",
        "noop": "FAIL",
        "authority-only": "FAIL",
        "alternate-path": "FAIL",
        "error": "INCONCLUSIVE",
    }
    manifests: dict[str, Mapping[str, Any]] = {}

    for name, expected_overall in expected.items():
        manifest = run_suite(SCENARIOS, BUILTINS[name], run_type="SELF_TEST")
        manifests[name] = manifest
        output = RESULTS / f"selftest-{name}.json"
        write_json(output, manifest)
    problems = evaluate_selftest(manifests, expected)

    if problems:
        print("AECP SELF_TEST: INSTRUMENT_FAILURE")
        for problem in problems:
            print(f"- {problem}")
        return 4

    print("AECP SELF_TEST: PASS")
    print("All four decision/effect cells reached; fixture reachability, divergence, binding, error and alternate-path controls behaved as expected.")
    return 0


def _validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    value = strict_json_loads(path.read_text(encoding="utf-8"))
    if args.kind == "scenario":
        validate_scenario(value)
    else:
        validate_manifest(value)
        if value["content_sha256"] != canonical_sha256(value["content"]):
            raise SchemaError("manifest content_sha256 does not match content")
    print(f"VALID {args.kind}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AECP local conformance exercise harness")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="exercise one adapter")
    adapter_group = run.add_mutually_exclusive_group()
    adapter_group.add_argument("--adapter", default="protected", help="builtin name or module:factory")
    adapter_group.add_argument(
        "--adapter-command",
        nargs="+",
        help="JSON-lines subprocess argv; place this option after other run options",
    )
    run.add_argument("--adapter-label", default="external-subprocess", help="path-free stable manifest label")
    run.add_argument("--run-type", choices=["SELF_TEST", "CONFORMANCE_EXERCISE"], default="CONFORMANCE_EXERCISE")
    run.add_argument("--output")
    run.set_defaults(func=_run)

    selftest = sub.add_parser("selftest", help="run instrument controls")
    selftest.set_defaults(func=_selftest)

    validate = sub.add_parser("validate", help="validate one scenario or manifest")
    validate.add_argument("kind", choices=["scenario", "manifest"])
    validate.add_argument("path")
    validate.set_defaults(func=_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except SchemaError as exc:
        print(f"SCHEMA_ERROR: {exc}", file=sys.stderr)
        return 3
    except (ValueError, TypeError, json.JSONDecodeError, OSError) as exc:
        print(f"HARNESS_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
