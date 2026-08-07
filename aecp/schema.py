"""Strict, standard-library validation for AECP scenarios and result manifests."""

from __future__ import annotations

import copy
import re
from typing import Any, Iterable, Mapping

from .canonical import canonical_sha256


class SchemaError(ValueError):
    pass


ID_PATTERN = re.compile(r"^AECP-[0-9]{2}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError(f"{path} must be an object")
    return value


def _list(value: Any, path: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise SchemaError(f"{path} must be an array")
    if nonempty and not value:
        raise SchemaError(f"{path} must not be empty")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaError(f"{path} must be a non-empty string")
    return value


def _strict_keys(value: Mapping[str, Any], allowed: Iterable[str], required: Iterable[str], path: str) -> None:
    allowed_set = set(allowed)
    missing = set(required) - set(value)
    unknown = set(value) - allowed_set
    if missing:
        raise SchemaError(f"{path} missing keys: {sorted(missing)}")
    if unknown:
        raise SchemaError(f"{path} unknown keys: {sorted(unknown)}")


def _get_path(value: Mapping[str, Any], dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise SchemaError(f"binding path not found: {dotted}")
        current = current[part]
    return current


def _without_path(value: Mapping[str, Any], dotted: str) -> Mapping[str, Any]:
    copied = copy.deepcopy(value)
    parts = dotted.split(".")
    current: Any = copied
    for part in parts[:-1]:
        current = current[part]
    current.pop(parts[-1])
    return copied


REQUEST_KEYS = {
    "operation", "target", "consumer", "use", "subject", "origin", "now", "context"
}
GRANT_KEYS = {
    "operation", "target", "consumer", "use", "subject", "origin", "epoch", "not_after", "nonce"
}
CONTEXT_KEYS = {
    "policy_epoch", "seen_nonces", "origin_qualified", "parent_authorities", "derived_authorities"
}


def _validate_request(value: Any, path: str) -> None:
    request = _object(value, path)
    _strict_keys(request, REQUEST_KEYS, REQUEST_KEYS, path)
    for key in ("operation", "target", "consumer", "use", "subject", "origin"):
        _string(request[key], f"{path}.{key}")
    if not isinstance(request["now"], int) or isinstance(request["now"], bool):
        raise SchemaError(f"{path}.now must be an integer logical time")
    context = _object(request["context"], f"{path}.context")
    _strict_keys(context, CONTEXT_KEYS, {"policy_epoch", "seen_nonces"}, f"{path}.context")
    if not isinstance(context["policy_epoch"], int) or isinstance(context["policy_epoch"], bool):
        raise SchemaError(f"{path}.context.policy_epoch must be an integer")
    seen_nonces = _list(context["seen_nonces"], f"{path}.context.seen_nonces")
    for index, nonce in enumerate(seen_nonces):
        _string(nonce, f"{path}.context.seen_nonces[{index}]")
    if len(seen_nonces) != len(set(seen_nonces)):
        raise SchemaError(f"{path}.context.seen_nonces must not contain duplicates")
    if "origin_qualified" in context and not isinstance(context["origin_qualified"], bool):
        raise SchemaError(f"{path}.context.origin_qualified must be a boolean")
    for authority_key in ("parent_authorities", "derived_authorities"):
        if authority_key in context:
            authorities = _list(context[authority_key], f"{path}.context.{authority_key}")
            for index, authority in enumerate(authorities):
                _string(authority, f"{path}.context.{authority_key}[{index}]")
            if len(authorities) != len(set(authorities)):
                raise SchemaError(f"{path}.context.{authority_key} must not contain duplicates")
    if request["operation"] == "artifact_reentry" and "origin_qualified" not in context:
        raise SchemaError(f"{path}.context.origin_qualified is required for artifact_reentry")
    if request["operation"] == "admit_derived_state":
        missing = {"parent_authorities", "derived_authorities"} - set(context)
        if missing:
            raise SchemaError(f"{path}.context missing derived-state keys: {sorted(missing)}")


def _validate_grant(value: Any, path: str) -> None:
    grant = _object(value, path)
    _strict_keys(grant, GRANT_KEYS, GRANT_KEYS, path)
    for key in ("operation", "target", "consumer", "use", "subject", "origin", "nonce"):
        _string(grant[key], f"{path}.{key}")
    for key in ("epoch", "not_after"):
        if not isinstance(grant[key], int) or isinstance(grant[key], bool):
            raise SchemaError(f"{path}.{key} must be an integer")


def _validate_case(value: Any, path: str, expected: str) -> None:
    case = _object(value, path)
    allowed = {"id", "request", "grants", "expect", "rationale", "tests_binding"}
    required = {"id", "request", "grants", "expect", "rationale"}
    if expected == "NON_FORMED":
        required.add("tests_binding")
    _strict_keys(case, allowed, required, path)
    _string(case["id"], f"{path}.id")
    _validate_request(case["request"], f"{path}.request")
    grants = _list(case["grants"], f"{path}.grants")
    for index, grant in enumerate(grants):
        _validate_grant(grant, f"{path}.grants[{index}]")
    if case["expect"] != expected:
        raise SchemaError(f"{path}.expect must be {expected}")
    _string(case["rationale"], f"{path}.rationale")
    if expected == "FORMED" and "tests_binding" in case:
        raise SchemaError(f"{path}.tests_binding is only valid on negative cases")
    if "tests_binding" in case:
        _string(case["tests_binding"], f"{path}.tests_binding")


def validate_scenario(value: Any) -> None:
    scenario = _object(value, "scenario")
    allowed = {
        "schema_version", "id", "name", "description", "source_status", "provenance",
        "grant_binding_fields", "binding_tests", "protected_surfaces", "synthetic_effect",
        "positive_control", "negative_cases", "trust_assumptions", "untested_paths",
    }
    _strict_keys(scenario, allowed, allowed, "scenario")
    if scenario["schema_version"] != "1.0":
        raise SchemaError("scenario.schema_version must be 1.0")
    scenario_id = _string(scenario["id"], "scenario.id")
    if not ID_PATTERN.match(scenario_id):
        raise SchemaError("scenario.id must match AECP-NN")
    _string(scenario["name"], "scenario.name")
    _string(scenario["description"], "scenario.description")
    if scenario["source_status"] not in {"SOURCE-DERIVED", "DESIGN-EXTENSION"}:
        raise SchemaError("scenario.source_status is invalid")

    provenance = _object(scenario["provenance"], "scenario.provenance")
    _strict_keys(
        provenance,
        {"source_id", "source_url", "section", "derivation"},
        {"source_id", "source_url", "section", "derivation"},
        "scenario.provenance",
    )
    for key in ("source_id", "source_url", "section"):
        _string(provenance[key], f"scenario.provenance.{key}")
    if provenance["derivation"] not in {"DIRECT", "ANALOGOUS", "EXTENSION"}:
        raise SchemaError("scenario.provenance.derivation is invalid")
    if scenario["source_status"] == "DESIGN-EXTENSION" and provenance["derivation"] != "EXTENSION":
        raise SchemaError("DESIGN-EXTENSION scenarios must use EXTENSION provenance")

    grant_fields = _list(scenario["grant_binding_fields"], "scenario.grant_binding_fields", nonempty=True)
    for field in grant_fields:
        if field not in {"operation", "target", "consumer", "use", "subject", "origin"}:
            raise SchemaError(f"unsupported grant binding field: {field}")
    if len(grant_fields) != len(set(grant_fields)):
        raise SchemaError("scenario.grant_binding_fields must not contain duplicates")
    binding_tests = _list(scenario["binding_tests"], "scenario.binding_tests", nonempty=True)
    for field in binding_tests:
        _string(field, "scenario.binding_tests[]")
    if len(binding_tests) != len(set(binding_tests)):
        raise SchemaError("scenario.binding_tests must not contain duplicates")
    required_tests = {
        "grant.presence",
        "request.context.policy_epoch",
        "grant.not_after",
        "request.context.seen_nonces",
        *(f"grant.{field}" for field in grant_fields),
    }
    missing_required_tests = required_tests - set(binding_tests)
    if missing_required_tests:
        raise SchemaError(f"missing required grant/lifecycle tests: {sorted(missing_required_tests)}")

    surfaces = _list(scenario["protected_surfaces"], "scenario.protected_surfaces", nonempty=True)
    surface_ids: list[str] = []
    for index, item in enumerate(surfaces):
        surface = _object(item, f"scenario.protected_surfaces[{index}]")
        _strict_keys(surface, {"id", "probe", "description"}, {"id", "probe", "description"}, f"scenario.protected_surfaces[{index}]")
        surface_ids.append(_string(surface["id"], f"scenario.protected_surfaces[{index}].id"))
        if surface["probe"] != "snapshot-diff-v1":
            raise SchemaError("RC2 protected surfaces must use snapshot-diff-v1")
        _string(surface["description"], f"scenario.protected_surfaces[{index}].description")
    if len(surface_ids) != len(set(surface_ids)):
        raise SchemaError("protected surface IDs must be unique")

    effect = _object(scenario["synthetic_effect"], "scenario.synthetic_effect")
    _strict_keys(effect, {"entries"}, {"entries"}, "scenario.synthetic_effect")
    entries = _list(effect["entries"], "scenario.synthetic_effect.entries", nonempty=True)
    effect_surfaces: set[str] = set()
    for index, entry_value in enumerate(entries):
        entry = _object(entry_value, f"scenario.synthetic_effect.entries[{index}]")
        _strict_keys(entry, {"surface", "key", "value"}, {"surface", "key", "value"}, f"scenario.synthetic_effect.entries[{index}]")
        effect_surfaces.add(_string(entry["surface"], f"scenario.synthetic_effect.entries[{index}].surface"))
        _string(entry["key"], f"scenario.synthetic_effect.entries[{index}].key")
    if effect_surfaces != set(surface_ids):
        raise SchemaError("synthetic_effect must exercise every declared protected surface exactly by surface set")

    _validate_case(scenario["positive_control"], "scenario.positive_control", "FORMED")
    if len(scenario["positive_control"]["grants"]) != 1:
        raise SchemaError("scenario.positive_control must present exactly one grant")
    negatives = _list(scenario["negative_cases"], "scenario.negative_cases", nonempty=True)
    case_ids = {scenario["positive_control"]["id"]}
    tested: list[str] = []
    for index, case in enumerate(negatives):
        _validate_case(case, f"scenario.negative_cases[{index}]", "NON_FORMED")
        if case["id"] in case_ids:
            raise SchemaError(f"duplicate case id: {case['id']}")
        case_ids.add(case["id"])
        tested.append(case["tests_binding"])

    if len(tested) != len(set(tested)):
        raise SchemaError("each tests_binding dimension must appear exactly once")
    if set(binding_tests) != set(tested):
        missing_tests = set(binding_tests) - set(tested)
        extra_tests = set(tested) - set(binding_tests)
        raise SchemaError(f"binding test set mismatch; missing={sorted(missing_tests)} extra={sorted(extra_tests)}")

    positive = scenario["positive_control"]
    for case in negatives:
        field = case["tests_binding"]
        if field == "grant.presence":
            if positive["request"] != case["request"] or len(positive["grants"]) != 1 or case["grants"]:
                raise SchemaError("grant.presence test must only remove the positive-control grant")
        elif field.startswith("grant."):
            key = field.split(".", 1)[1]
            if len(positive["grants"]) != 1 or len(case["grants"]) != 1:
                raise SchemaError(f"{field} test requires exactly one grant")
            if positive["request"] != case["request"]:
                raise SchemaError(f"{field} test must not change the request")
            if _get_path(positive["grants"][0], key) == _get_path(case["grants"][0], key):
                raise SchemaError(f"{field} test does not change {key}")
            if _without_path(positive["grants"][0], key) != _without_path(case["grants"][0], key):
                raise SchemaError(f"{field} test changes more than {key}")
        elif field.startswith("request."):
            key = field.split(".", 1)[1]
            if positive["grants"] != case["grants"]:
                raise SchemaError(f"{field} test must not change grants")
            positive_value = _get_path(positive["request"], key)
            negative_value = _get_path(case["request"], key)
            if isinstance(positive_value, Mapping) or isinstance(negative_value, Mapping):
                raise SchemaError(f"{field} test must identify a leaf value, not an object")
            if positive_value == negative_value:
                raise SchemaError(f"{field} test does not change {key}")
            if _without_path(positive["request"], key) != _without_path(case["request"], key):
                raise SchemaError(f"{field} test changes more than {key}")
        else:
            raise SchemaError(f"binding test path must start with grant. or request.: {field}")

    for key in ("trust_assumptions", "untested_paths"):
        values = _list(scenario[key], f"scenario.{key}")
        for index, item in enumerate(values):
            _string(item, f"scenario.{key}[{index}]")


def validate_manifest(value: Any) -> None:
    manifest = _object(value, "manifest")
    _strict_keys(manifest, {"manifest_version", "content_sha256", "content"}, {"manifest_version", "content_sha256", "content"}, "manifest")
    if manifest["manifest_version"] != "1.0":
        raise SchemaError("manifest.manifest_version must be 1.0")
    if not isinstance(manifest["content_sha256"], str) or not SHA_PATTERN.match(manifest["content_sha256"]):
        raise SchemaError("manifest.content_sha256 must be lowercase SHA-256")
    content = _object(manifest["content"], "manifest.content")
    _strict_keys(
        content,
        {"profile_version", "run_type", "implementation", "scope_note", "overall", "scenarios"},
        {"profile_version", "run_type", "implementation", "scope_note", "overall", "scenarios"},
        "manifest.content",
    )
    _string(content["profile_version"], "manifest.content.profile_version")
    if content["run_type"] not in {"SELF_TEST", "CONFORMANCE_EXERCISE"}:
        raise SchemaError("manifest.content.run_type is invalid")
    implementation = _object(content["implementation"], "manifest.content.implementation")
    _strict_keys(
        implementation,
        {"api_version", "id", "version", "kind", "description"},
        {"api_version", "id", "version", "kind", "description"},
        "manifest.content.implementation",
    )
    for key in implementation:
        _string(implementation[key], f"manifest.content.implementation.{key}")
    _string(content["scope_note"], "manifest.content.scope_note")
    if content["overall"] not in {"PASS", "FAIL", "INCONCLUSIVE"}:
        raise SchemaError("manifest.content.overall is invalid")
    scenarios = _list(content["scenarios"], "manifest.content.scenarios", nonempty=True)
    scenario_statuses: set[str] = set()
    for index, item in enumerate(scenarios):
        record = _object(item, f"manifest.content.scenarios[{index}]")
        required = {
            "scenario_id", "scenario_name", "source_status", "fixture_path", "fixture_file_sha256",
            "fixture_canonical_sha256", "protected_surfaces", "probe_contract", "trust_assumptions",
            "untested_paths", "evidence_tier", "status", "cases",
        }
        _strict_keys(record, required, required, f"manifest.content.scenarios[{index}]")
        scenario_id = _string(record["scenario_id"], f"scenario[{index}].scenario_id")
        if not ID_PATTERN.match(scenario_id):
            raise SchemaError("manifest scenario_id must match AECP-NN")
        _string(record["scenario_name"], f"scenario[{index}].scenario_name")
        if record["source_status"] not in {"SOURCE-DERIVED", "DESIGN-EXTENSION"}:
            raise SchemaError("manifest source_status is invalid")
        fixture_path = _string(record["fixture_path"], f"scenario[{index}].fixture_path")
        if not fixture_path.startswith("scenarios/") or ".." in fixture_path.split("/"):
            raise SchemaError("manifest fixture_path must be a relative scenarios/ path")
        if not isinstance(record["fixture_file_sha256"], str) or not isinstance(record["fixture_canonical_sha256"], str):
            raise SchemaError("fixture digests must be strings")
        if not SHA_PATTERN.match(record["fixture_file_sha256"]) or not SHA_PATTERN.match(record["fixture_canonical_sha256"]):
            raise SchemaError("fixture digests must be lowercase SHA-256")
        for surface in _list(record["protected_surfaces"], "protected_surfaces", nonempty=True):
            _string(surface, "protected_surfaces[]")
        if record["probe_contract"] != "snapshot-diff-v1":
            raise SchemaError("manifest probe_contract is invalid")
        for list_name in ("trust_assumptions", "untested_paths"):
            for entry in _list(record[list_name], list_name):
                _string(entry, f"{list_name}[]")
        if record["status"] not in {"PASS", "FAIL", "INCONCLUSIVE"}:
            raise SchemaError("scenario status is invalid")
        scenario_statuses.add(record["status"])
        if record["evidence_tier"] not in {"EXERCISED", "PARTIAL"}:
            raise SchemaError("scenario evidence tier is invalid")
        cases = _list(record["cases"], "cases", nonempty=True)
        case_verdicts: list[str] = []
        for case_index, case_value in enumerate(cases):
            case = _object(case_value, "case")
            case_required = {
                "case_id", "kind", "expected", "decision", "decision_reason", "observation", "verdict",
                "divergence", "declared_surface_changes", "undeclared_surface_changes", "probes", "error",
            }
            _strict_keys(case, case_required, case_required, f"case[{case_index}]")
            _string(case["case_id"], f"case[{case_index}].case_id")
            if case["kind"] not in {"POSITIVE_CONTROL", "NEGATIVE"}:
                raise SchemaError("case kind is invalid")
            if case["expected"] not in {"FORMED", "NON_FORMED"}:
                raise SchemaError("case expected is invalid")
            if case["decision"] not in {"ALLOW", "DENY", "ERROR"}:
                raise SchemaError("case decision is invalid")
            _string(case["decision_reason"], f"case[{case_index}].decision_reason")
            if case["observation"] not in {"FORMED", "NOT_FORMED", "ERROR", "TIMEOUT"}:
                raise SchemaError("case observation is invalid")
            if case["verdict"] not in {"AS_EXPECTED", "UNEXPECTED_FORMATION", "UNEXPECTED_NON_FORMATION", "UNEXPECTED_PARTIAL_FORMATION", "INCONCLUSIVE"}:
                raise SchemaError("case verdict is invalid")
            case_verdicts.append(case["verdict"])
            if case["divergence"] not in {"NONE", "DENIED_BUT_FORMED", "ALLOWED_BUT_NOT_FORMED", "FORMED_DURING_ERROR"}:
                raise SchemaError("case divergence is invalid")
            change_lists: dict[str, list[Any]] = {}
            for change_list in ("declared_surface_changes", "undeclared_surface_changes"):
                change_lists[change_list] = _list(case[change_list], change_list)
                for change_index, change_value in enumerate(change_lists[change_list]):
                    change = _object(change_value, f"{change_list}[{change_index}]")
                    _strict_keys(change, {"surface", "key", "change", "before_digest", "after_digest"}, {"surface", "key", "change", "before_digest", "after_digest"}, f"{change_list}[{change_index}]")
                    _string(change["surface"], "change.surface")
                    _string(change["key"], "change.key")
                    if change["change"] not in {"ADDED", "MODIFIED", "DELETED"}:
                        raise SchemaError("surface change kind is invalid")
                    for digest_name in ("before_digest", "after_digest"):
                        digest = change[digest_name]
                        if digest is not None and (not isinstance(digest, str) or not SHA_PATTERN.match(digest)):
                            raise SchemaError("surface change digest is invalid")
            declared_surfaces = {change["surface"] for change in change_lists["declared_surface_changes"]}
            undeclared_surfaces = {change["surface"] for change in change_lists["undeclared_surface_changes"]}
            protected_set = set(record["protected_surfaces"])
            if not declared_surfaces.issubset(protected_set):
                raise SchemaError("declared surface changes contain a non-protected surface")
            if undeclared_surfaces & protected_set:
                raise SchemaError("undeclared surface changes contain a protected surface")
            change_pairs = [
                (change["surface"], change["key"])
                for values in change_lists.values()
                for change in values
            ]
            if len(change_pairs) != len(set(change_pairs)):
                raise SchemaError("surface changes contain duplicate surface/key pairs")
            probes = _list(case["probes"], "case.probes", nonempty=True)
            observed_by_surface: dict[str, str] = {}
            for probe_index, probe_value in enumerate(probes):
                probe = _object(probe_value, f"probe[{probe_index}]")
                _strict_keys(probe, {"surface", "probe", "observed"}, {"surface", "probe", "observed"}, f"probe[{probe_index}]")
                _string(probe["surface"], "probe.surface")
                if probe["probe"] != "snapshot-diff-v1" or probe["observed"] not in {"PRESENT", "ABSENT"}:
                    raise SchemaError("probe record is invalid")
                if probe["surface"] in observed_by_surface:
                    raise SchemaError("probe surfaces must be unique")
                observed_by_surface[probe["surface"]] = probe["observed"]
            if set(observed_by_surface) != protected_set:
                raise SchemaError("probe surfaces must exactly match protected surfaces")
            for surface, observed in observed_by_surface.items():
                expected_probe = "PRESENT" if surface in declared_surfaces else "ABSENT"
                if observed != expected_probe:
                    raise SchemaError(f"probe observation for {surface} is inconsistent with surface changes")
            if case["error"] is not None and not isinstance(case["error"], str):
                raise SchemaError("case error must be string or null")
            if case["error"] is not None and case["decision"] != "ERROR":
                raise SchemaError("case error requires decision ERROR")

            has_changes = bool(change_pairs)
            if case["observation"] == "FORMED" and not has_changes:
                raise SchemaError("FORMED observation requires a surface change")
            if case["observation"] == "NOT_FORMED" and has_changes:
                raise SchemaError("NOT_FORMED observation cannot contain a surface change")
            if case["observation"] in {"ERROR", "TIMEOUT"}:
                if case["decision"] != "ERROR":
                    raise SchemaError("ERROR/TIMEOUT observation requires decision ERROR")
                expected_verdict = "UNEXPECTED_FORMATION" if has_changes else "INCONCLUSIVE"
                expected_divergence = "FORMED_DURING_ERROR" if has_changes else "NONE"
            else:
                if case["expected"] == "NON_FORMED":
                    expected_verdict = "UNEXPECTED_FORMATION" if has_changes else "AS_EXPECTED"
                elif undeclared_surfaces:
                    expected_verdict = "UNEXPECTED_FORMATION"
                elif declared_surfaces == protected_set:
                    expected_verdict = "AS_EXPECTED"
                elif not declared_surfaces:
                    expected_verdict = "UNEXPECTED_NON_FORMATION"
                else:
                    expected_verdict = "UNEXPECTED_PARTIAL_FORMATION"
                if case["decision"] == "DENY" and case["observation"] == "FORMED":
                    expected_divergence = "DENIED_BUT_FORMED"
                elif case["decision"] == "ALLOW" and case["observation"] == "NOT_FORMED":
                    expected_divergence = "ALLOWED_BUT_NOT_FORMED"
                else:
                    expected_divergence = "NONE"
            if case["verdict"] != expected_verdict:
                raise SchemaError(f"case verdict is inconsistent; expected {expected_verdict}")
            if case["divergence"] != expected_divergence:
                raise SchemaError(f"case divergence is inconsistent; expected {expected_divergence}")

        positive_cases = [case for case in cases if case["kind"] == "POSITIVE_CONTROL"]
        if len(positive_cases) != 1 or cases[0]["kind"] != "POSITIVE_CONTROL":
            raise SchemaError("manifest scenario must start with exactly one positive control")
        if positive_cases[0]["expected"] != "FORMED":
            raise SchemaError("positive control must expect FORMED")
        if any(case["expected"] != "NON_FORMED" for case in cases[1:]):
            raise SchemaError("negative cases must expect NON_FORMED")

        has_divergence = any(case["divergence"] != "NONE" for case in cases)
        expected_status = "FAIL" if has_divergence or any(verdict not in {"AS_EXPECTED", "INCONCLUSIVE"} for verdict in case_verdicts) else ("INCONCLUSIVE" if "INCONCLUSIVE" in case_verdicts else "PASS")
        if record["status"] != expected_status:
            raise SchemaError(f"scenario status {record['status']} inconsistent with cases; expected {expected_status}")
        expected_tier = "PARTIAL" if expected_status == "INCONCLUSIVE" else "EXERCISED"
        if record["evidence_tier"] != expected_tier:
            raise SchemaError(f"scenario evidence tier {record['evidence_tier']} inconsistent with status; expected {expected_tier}")

    expected_overall = "FAIL" if "FAIL" in scenario_statuses else ("INCONCLUSIVE" if "INCONCLUSIVE" in scenario_statuses else "PASS")
    if content["overall"] != expected_overall:
        raise SchemaError(f"overall {content['overall']} inconsistent with scenario statuses; expected {expected_overall}")
    if manifest["content_sha256"] != canonical_sha256(content):
        raise SchemaError("manifest content_sha256 does not match content")
