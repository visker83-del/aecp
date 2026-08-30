"""Built-in adapters plus a neutral Python/subprocess adapter contract."""

from __future__ import annotations

import importlib
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol, Sequence

from .policy import qualifies
from .canonical import strict_json_loads
from .world import EffectPort


AECP_ADAPTER_API = "1.0"
ADAPTER_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class Adapter(Protocol):
    def describe(self) -> Mapping[str, Any]: ...
    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]: ...


def _emit_declared(request: Mapping[str, Any], port: EffectPort) -> None:
    for entry in request.get("synthetic_effect", {}).get("entries", []):
        port.emit(entry["surface"], entry["key"], entry["value"])


@dataclass
class _Builtin:
    adapter_id: str
    description: str

    def describe(self) -> Mapping[str, Any]:
        return {
            "api_version": AECP_ADAPTER_API,
            "id": self.adapter_id,
            "version": "1.0",
            "kind": "illustrative-local",
            "description": self.description,
        }


class ProtectedAdapter(_Builtin):
    """A self-contained illustrative control.

    Qualification and synthetic actuation are implemented together here, so
    `if allowed: emit` is correct. It is not a template for wrapping an
    external control: a wrapper built this way derives the emission from the
    decision and can never observe a denial that still formed an effect. See
    "Wrapping an external control" in ADAPTER_CONTRACT.md.
    """

    def __init__(self) -> None:
        super().__init__("illustrative-protected", "Exact-binding example control")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        allowed, reason = qualifies(request)
        if allowed:
            _emit_declared(request, port)
        return {"decision": "ALLOW" if allowed else "DENY", "reason": reason}


class PermissiveAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-permissive", "Unmediated baseline")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        _emit_declared(request, port)
        return {"decision": "ALLOW", "reason": "unmediated_baseline"}


class LeakyAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-leaky", "Returns DENY but still emits")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        _emit_declared(request, port)
        return {"decision": "DENY", "reason": "intentional_test_leak"}


class DeadendAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-deadend", "Blocks every request")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        return {"decision": "DENY", "reason": "intentional_test_deadend"}


class NoopAllowAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-noop-allow", "Returns ALLOW without emitting")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        return {"decision": "ALLOW", "reason": "intentional_test_noop"}


class AuthorityOnlyAdapter(_Builtin):
    """Shadow-build-style adapter that ignores target, consumer, use and freshness."""

    def __init__(self) -> None:
        super().__init__("illustrative-authority-only", "Deliberately incomplete binding control")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        operation = request.get("operation")
        allowed = any(grant.get("operation") == operation for grant in request.get("presented_grants", []))
        if allowed:
            _emit_declared(request, port)
        return {
            "decision": "ALLOW" if allowed else "DENY",
            "reason": "operation_only_match" if allowed else "operation_missing",
        }


class AlternatePathAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-alternate-path", "Writes an undeclared alternate surface")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        port.emit("unregistered://alternate-spool", request["request_token"], {"bypass": True})
        return {"decision": "DENY", "reason": "intentional_undeclared_path"}


class ErrorAdapter(_Builtin):
    def __init__(self) -> None:
        super().__init__("illustrative-error", "Raises to test inconclusive handling")

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        raise RuntimeError("intentional adapter failure")


class SubprocessAdapter:
    """One-request/one-response JSON-lines bridge with validate-before-apply semantics."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        label: str = "external-subprocess",
        timeout_seconds: float = 30,
    ) -> None:
        if not command:
            raise ValueError("adapter command must not be empty")
        if not isinstance(label, str) or not ADAPTER_LABEL_PATTERN.fullmatch(label):
            raise ValueError(
                "adapter label must be 1-128 ASCII letters, digits, dots, underscores or hyphens, "
                "and must start with a letter or digit"
            )
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("adapter timeout_seconds must be positive")
        self._command = tuple(command)
        self._label = label
        self._timeout_seconds = timeout_seconds

    def describe(self) -> Mapping[str, Any]:
        return {
            "api_version": AECP_ADAPTER_API,
            "id": f"subprocess:{self._label}",
            "version": "external",
            "kind": "external-subprocess",
            "description": "User-supplied subprocess adapter",
        }

    def handle(self, request: Mapping[str, Any], port: EffectPort) -> Mapping[str, str]:
        completed = subprocess.run(
            self._command,
            input=json.dumps(request, sort_keys=True) + "\n",
            text=True,
            capture_output=True,
            timeout=self._timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"adapter subprocess exited {completed.returncode}")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError("adapter subprocess must emit exactly one non-empty JSON line")
        response = strict_json_loads(lines[0])
        if not isinstance(response, dict):
            raise ValueError("adapter subprocess response must be an object")
        allowed_keys = {"decision", "reason", "emissions"}
        unknown = set(response) - allowed_keys
        if unknown:
            raise ValueError(f"adapter subprocess response has unknown keys: {sorted(unknown)}")
        decision = response.get("decision")
        if decision not in {"ALLOW", "DENY", "ERROR"}:
            raise ValueError("adapter subprocess decision must be ALLOW, DENY, or ERROR")
        reason = response.get("reason", "external")
        if not isinstance(reason, str) or not reason:
            raise ValueError("adapter subprocess reason must be a non-empty string")
        emissions = response.get("emissions", [])
        if not isinstance(emissions, list):
            raise ValueError("adapter subprocess emissions must be an array")
        validated_emissions: list[dict[str, Any]] = []
        for index, entry in enumerate(emissions):
            if not isinstance(entry, dict) or set(entry) != {"surface", "key", "value"}:
                raise ValueError(f"adapter subprocess emission[{index}] has invalid keys")
            if not isinstance(entry["surface"], str) or not entry["surface"]:
                raise ValueError(f"adapter subprocess emission[{index}].surface is invalid")
            if not isinstance(entry["key"], str) or not entry["key"]:
                raise ValueError(f"adapter subprocess emission[{index}].key is invalid")
            validated_emissions.append(entry)

        # Apply only after the complete response has passed protocol validation.
        for entry in validated_emissions:
            port.emit(entry["surface"], entry["key"], entry["value"])
        return {"decision": decision, "reason": reason}


BUILTINS: dict[str, Callable[[], Adapter]] = {
    "protected": ProtectedAdapter,
    "permissive": PermissiveAdapter,
    "leaky": LeakyAdapter,
    "deadend": DeadendAdapter,
    "noop": NoopAllowAdapter,
    "authority-only": AuthorityOnlyAdapter,
    "alternate-path": AlternatePathAdapter,
    "error": ErrorAdapter,
}


def load_adapter(spec: str) -> Callable[[], Adapter]:
    if spec in BUILTINS:
        return BUILTINS[spec]
    if ":" not in spec:
        raise ValueError("adapter must be a builtin name or module:factory")
    module_name, factory_name = spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name)
    except Exception as exc:
        raise ValueError(f"cannot load adapter {spec}: {exc}") from exc
    if not callable(factory):
        raise ValueError("adapter factory is not callable")
    return factory
