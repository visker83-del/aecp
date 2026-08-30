from __future__ import annotations

import copy
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from aecp.adapters import (
    AlternatePathAdapter,
    AuthorityOnlyAdapter,
    DeadendAdapter,
    ErrorAdapter,
    LeakyAdapter,
    NoopAllowAdapter,
    PermissiveAdapter,
    ProtectedAdapter,
    SubprocessAdapter,
)
from aecp.canonical import canonical_sha256, strict_json_loads, write_json
from aecp.cli import evaluate_selftest
from aecp.runner import run_suite
from aecp.policy import qualifies
from aecp.schema import SchemaError, validate_manifest, validate_scenario
from aecp.world import observe_surface_changes
from aecp.world import SyntheticWorld


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"


class HarnessTests(unittest.TestCase):
    def run_adapter(self, factory):
        return run_suite(SCENARIOS, factory, run_type="SELF_TEST")

    def test_protected_reference_passes(self):
        manifest = self.run_adapter(ProtectedAdapter)
        self.assertEqual("PASS", manifest["content"]["overall"])

    def test_permissive_baseline_exposes_every_negative(self):
        manifest = self.run_adapter(PermissiveAdapter)
        self.assertEqual("FAIL", manifest["content"]["overall"])
        for scenario in manifest["content"]["scenarios"]:
            for case in scenario["cases"]:
                if case["kind"] == "NEGATIVE":
                    self.assertEqual("FORMED", case["observation"])

    def test_decision_and_effect_are_independent(self):
        self.assertEqual(("before", "after"), tuple(inspect.signature(observe_surface_changes).parameters))
        leaky = self.run_adapter(LeakyAdapter)
        noop = self.run_adapter(NoopAllowAdapter)
        leaky_divergence = {
            case["divergence"]
            for scenario in leaky["content"]["scenarios"]
            for case in scenario["cases"]
        }
        noop_divergence = {
            case["divergence"]
            for scenario in noop["content"]["scenarios"]
            for case in scenario["cases"]
        }
        self.assertIn("DENIED_BUT_FORMED", leaky_divergence)
        self.assertIn("ALLOWED_BUT_NOT_FORMED", noop_divergence)

    def test_selective_decision_effect_divergence_cannot_pass(self):
        class DenyQualifiedFormation(ProtectedAdapter):
            def handle(self, request, port):
                allowed, reason = qualifies(request)
                if allowed:
                    for entry in request["synthetic_effect"]["entries"]:
                        port.emit(entry["surface"], entry["key"], entry["value"])
                return {"decision": "DENY", "reason": reason}

        class AllowQualifiedOnly(ProtectedAdapter):
            def handle(self, request, port):
                allowed, reason = qualifies(request)
                if allowed:
                    for entry in request["synthetic_effect"]["entries"]:
                        port.emit(entry["surface"], entry["key"], entry["value"])
                return {"decision": "ALLOW", "reason": reason}

        denied_positives = self.run_adapter(DenyQualifiedFormation)
        self.assertEqual("FAIL", denied_positives["content"]["overall"])
        for scenario in denied_positives["content"]["scenarios"]:
            positive = scenario["cases"][0]
            self.assertEqual("AS_EXPECTED", positive["verdict"])
            self.assertEqual("DENIED_BUT_FORMED", positive["divergence"])
            self.assertEqual("FAIL", scenario["status"])

        allowed_negatives = self.run_adapter(AllowQualifiedOnly)
        self.assertEqual("FAIL", allowed_negatives["content"]["overall"])
        for scenario in allowed_negatives["content"]["scenarios"]:
            negatives = scenario["cases"][1:]
            self.assertTrue(negatives)
            self.assertTrue(all(case["verdict"] == "AS_EXPECTED" for case in negatives))
            self.assertTrue(all(case["divergence"] == "ALLOWED_BUT_NOT_FORMED" for case in negatives))
            self.assertEqual("FAIL", scenario["status"])

    def test_authority_only_control_fails_binding_cases(self):
        manifest = self.run_adapter(AuthorityOnlyAdapter)
        self.assertEqual("FAIL", manifest["content"]["overall"])
        unexpected = [
            case
            for scenario in manifest["content"]["scenarios"]
            for case in scenario["cases"]
            if case["verdict"] != "AS_EXPECTED"
        ]
        self.assertTrue(unexpected)

    def test_aecp07_uses_a_fresh_grant_and_isolates_authority_amplification(self):
        path = SCENARIOS / "aecp-07_derived_state_authority_amplification.json"
        scenario = json.loads(path.read_text(encoding="utf-8"))
        positive = scenario["positive_control"]
        amplified = next(
            case for case in scenario["negative_cases"]
            if case["tests_binding"] == "request.context.derived_authorities"
        )
        self.assertEqual(1, len(positive["grants"]))
        self.assertEqual(positive["grants"], amplified["grants"])
        positive_request = copy.deepcopy(positive["request"])
        amplified_request = copy.deepcopy(amplified["request"])
        positive_derived = positive_request["context"].pop("derived_authorities")
        amplified_derived = amplified_request["context"].pop("derived_authorities")
        self.assertEqual(positive_request, amplified_request)
        self.assertNotEqual(positive_derived, amplified_derived)

    def test_adapter_request_withholds_human_readable_case_oracles(self):
        observed_keys = []

        class RecordingProtected(ProtectedAdapter):
            def handle(self, request, port):
                observed_keys.append(set(request))
                return super().handle(request, port)

        manifest = self.run_adapter(RecordingProtected)
        self.assertEqual("PASS", manifest["content"]["overall"])
        self.assertTrue(observed_keys)
        for keys in observed_keys:
            self.assertIn("request_token", keys)
            self.assertNotIn("scenario_id", keys)
            self.assertNotIn("case_id", keys)

    def test_undeclared_surface_is_detected(self):
        manifest = self.run_adapter(AlternatePathAdapter)
        changes = [
            case["undeclared_surface_changes"]
            for scenario in manifest["content"]["scenarios"]
            for case in scenario["cases"]
        ]
        self.assertTrue(any(changes))
        self.assertEqual("FAIL", manifest["content"]["overall"])

    def test_adapter_error_is_inconclusive_not_nonformation(self):
        manifest = self.run_adapter(ErrorAdapter)
        self.assertEqual("INCONCLUSIVE", manifest["content"]["overall"])
        for scenario in manifest["content"]["scenarios"]:
            for case in scenario["cases"]:
                self.assertEqual("ERROR", case["observation"])
                self.assertEqual("INCONCLUSIVE", case["verdict"])

    def test_effect_observed_before_adapter_error_is_failure(self):
        class EmitThenError(ProtectedAdapter):
            def handle(self, request, port):
                entry = request["synthetic_effect"]["entries"][0]
                port.emit(entry["surface"], entry["key"], entry["value"])
                raise RuntimeError("after effect")

        manifest = self.run_adapter(EmitThenError)
        self.assertEqual("FAIL", manifest["content"]["overall"])
        first_case = manifest["content"]["scenarios"][0]["cases"][0]
        self.assertEqual("UNEXPECTED_FORMATION", first_case["verdict"])
        self.assertEqual("FORMED_DURING_ERROR", first_case["divergence"])

    def test_effect_port_validates_value_before_state_mutation(self):
        world = SyntheticWorld(["declared"])
        before = world.snapshot()
        with self.assertRaises(TypeError):
            world.port().emit("declared", "bad", {1, 2})
        self.assertEqual(before, world.snapshot())

        class NonJsonEmission(ProtectedAdapter):
            def handle(self, request, port):
                entry = request["synthetic_effect"]["entries"][0]
                port.emit(entry["surface"], entry["key"], {1, 2})
                return {"decision": "ALLOW", "reason": "unreachable"}

        manifest = self.run_adapter(NonJsonEmission)
        self.assertEqual("INCONCLUSIVE", manifest["content"]["overall"])

    def test_manifest_is_byte_deterministic(self):
        first = self.run_adapter(ProtectedAdapter)
        second = self.run_adapter(ProtectedAdapter)
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as directory:
            one = Path(directory) / "one.json"
            two = Path(directory) / "two.json"
            write_json(one, first)
            write_json(two, second)
            self.assertEqual(one.read_bytes(), two.read_bytes())

    def test_manifest_hash_and_strict_validation(self):
        manifest = self.run_adapter(ProtectedAdapter)
        validate_manifest(manifest)
        self.assertEqual(manifest["content_sha256"], canonical_sha256(manifest["content"]))
        invalid = copy.deepcopy(manifest)
        invalid["unexpected"] = True
        with self.assertRaises(SchemaError):
            validate_manifest(invalid)

    def test_scenario_validation_is_strict(self):
        scenario_path = next(iter(sorted(SCENARIOS.glob("aecp-*.json"))))
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        validate_scenario(scenario)
        scenario["unexpected"] = True
        with self.assertRaises(SchemaError):
            validate_scenario(scenario)

    def test_context_types_and_duplicate_json_keys_are_rejected(self):
        scenario_path = SCENARIOS / "aecp-04_cross_agent_artifact_reentry.json"
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        scenario["positive_control"]["request"]["context"]["origin_qualified"] = "yes"
        with self.assertRaises(SchemaError):
            validate_scenario(scenario)

        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        scenario["positive_control"]["request"]["context"]["seen_nonces"] = ["used", "used"]
        with self.assertRaises(SchemaError):
            validate_scenario(scenario)

        with self.assertRaises(ValueError):
            strict_json_loads('{"id":"first","id":"second"}')
        with self.assertRaises(ValueError):
            strict_json_loads('{"value":1e400}')

    def test_subprocess_adapter_label_rejects_paths_and_control_characters(self):
        for label in ("../escape", "folder/name", "line\nbreak", "tab\tlabel", " leading"):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    SubprocessAdapter([sys.executable, "-c", "pass"], label=label)

    def test_subprocess_bridge_applies_emissions_to_parent_world(self):
        script = ROOT / "tests" / "fixtures" / "permissive_subprocess.py"
        factory = lambda: SubprocessAdapter([sys.executable, str(script)], label="test-fixture")
        manifest = self.run_adapter(factory)
        self.assertEqual("FAIL", manifest["content"]["overall"])
        first_case = manifest["content"]["scenarios"][0]["cases"][0]
        self.assertEqual("FORMED", first_case["observation"])
        self.assertEqual("subprocess:test-fixture", manifest["content"]["implementation"]["id"])

    def test_documented_example_adapter_passes_as_shipped(self):
        """The copyable example in examples/ must keep working, or the docs lie."""
        script = ROOT / "examples" / "subprocess_adapter.py"
        factory = lambda: SubprocessAdapter([sys.executable, str(script)], label="example-subprocess")
        env = {k: v for k, v in os.environ.items() if k != "AECP_EXAMPLE_FAULT"}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            manifest = self.run_adapter(factory)
        self.assertEqual("PASS", manifest["content"]["overall"])

    def test_documented_example_wiring_check_is_sensitive(self):
        """The fault switch must actually reach the effect port.

        This is the property the example teaches integrators to verify. If a
        deliberate leak inside the candidate's actuation path stops producing
        DENIED_BUT_FORMED, the example no longer demonstrates a non-circular
        wiring and the instructions in examples/README.md are wrong.
        """
        script = ROOT / "examples" / "subprocess_adapter.py"
        factory = lambda: SubprocessAdapter([sys.executable, str(script)], label="example-fault")
        with unittest.mock.patch.dict(os.environ, {"AECP_EXAMPLE_FAULT": "leak-after-deny"}):
            manifest = self.run_adapter(factory)
        self.assertEqual("FAIL", manifest["content"]["overall"])
        divergences = {
            case["divergence"]
            for scenario in manifest["content"]["scenarios"]
            for case in scenario["cases"]
        }
        self.assertIn("DENIED_BUT_FORMED", divergences)

    def test_subprocess_validates_complete_response_before_emitting(self):
        payload = json.dumps({
            "reason": "missing decision",
            "emissions": [{"surface": "declared", "key": "k", "value": True}],
        })
        adapter = SubprocessAdapter(
            [sys.executable, "-c", f"print({payload!r})"],
            label="invalid-response",
        )
        world = SyntheticWorld(["declared"])
        before = world.snapshot()
        with self.assertRaises(ValueError):
            adapter.handle({}, world.port())
        self.assertEqual(before, world.snapshot())

    def test_subprocess_nonzero_malformed_and_timeout_fail_closed_as_errors(self):
        world = SyntheticWorld(["declared"])
        commands = [
            SubprocessAdapter([sys.executable, "-c", "raise SystemExit(7)"], label="nonzero"),
            SubprocessAdapter([sys.executable, "-c", "print('not-json')"], label="malformed"),
            SubprocessAdapter(
                [sys.executable, "-c", "import time; time.sleep(1)"],
                label="timeout",
                timeout_seconds=0.02,
            ),
        ]
        for adapter in commands:
            with self.assertRaises((RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired)):
                adapter.handle({}, world.port())

    def test_cli_failure_exit_code(self):
        completed = subprocess.run(
            [sys.executable, "-B", "verify.py", "run", "--adapter", "leaky"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, completed.returncode)

    def test_instrument_failure_is_reachable(self):
        names = {
            "protected": ProtectedAdapter,
            "permissive": PermissiveAdapter,
            "leaky": LeakyAdapter,
            "deadend": DeadendAdapter,
            "noop": NoopAllowAdapter,
            "authority-only": AuthorityOnlyAdapter,
            "alternate-path": AlternatePathAdapter,
            "error": ErrorAdapter,
        }
        expected = {
            "protected": "PASS", "permissive": "FAIL", "leaky": "FAIL", "deadend": "FAIL",
            "noop": "FAIL", "authority-only": "FAIL", "alternate-path": "FAIL", "error": "INCONCLUSIVE",
        }
        manifests = {name: self.run_adapter(factory) for name, factory in names.items()}
        manifests["protected"] = copy.deepcopy(manifests["protected"])
        manifests["protected"]["content"]["overall"] = "FAIL"
        problems = evaluate_selftest(manifests, expected)
        self.assertTrue(problems)

    def test_selftest_evaluator_checks_each_instrument_control(self):
        names = {
            "protected": ProtectedAdapter,
            "permissive": PermissiveAdapter,
            "leaky": LeakyAdapter,
            "deadend": DeadendAdapter,
            "noop": NoopAllowAdapter,
            "authority-only": AuthorityOnlyAdapter,
            "alternate-path": AlternatePathAdapter,
            "error": ErrorAdapter,
        }
        expected = {
            "protected": "PASS", "permissive": "FAIL", "leaky": "FAIL", "deadend": "FAIL",
            "noop": "FAIL", "authority-only": "FAIL", "alternate-path": "FAIL", "error": "INCONCLUSIVE",
        }
        manifests = {name: self.run_adapter(factory) for name, factory in names.items()}
        self.assertEqual([], evaluate_selftest(manifests, expected))

        vacuous = copy.deepcopy(manifests)
        negative = next(
            case for scenario in vacuous["permissive"]["content"]["scenarios"]
            for case in scenario["cases"] if case["kind"] == "NEGATIVE"
        )
        negative["observation"] = "NOT_FORMED"
        self.assertTrue(any("fixture reachability failure" in item for item in evaluate_selftest(vacuous, expected)))

        no_leak_signal = copy.deepcopy(manifests)
        for scenario in no_leak_signal["leaky"]["content"]["scenarios"]:
            for case in scenario["cases"]:
                case["divergence"] = "NONE"
        self.assertTrue(any("DENIED_BUT_FORMED" in item for item in evaluate_selftest(no_leak_signal, expected)))

        no_alternate_signal = copy.deepcopy(manifests)
        for scenario in no_alternate_signal["alternate-path"]["content"]["scenarios"]:
            for case in scenario["cases"]:
                case["undeclared_surface_changes"] = []
        self.assertTrue(any("undeclared alternate" in item for item in evaluate_selftest(no_alternate_signal, expected)))


if __name__ == "__main__":
    unittest.main()
