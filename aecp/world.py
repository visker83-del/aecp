"""Policy-free synthetic effect world and independent surface observation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping

from .canonical import canonical_sha256


Snapshot = Dict[str, Dict[str, str]]


@dataclass(frozen=True)
class SurfaceChange:
    surface: str
    key: str
    change: str
    before_digest: str | None
    after_digest: str | None


class SyntheticWorld:
    """A local state container that deliberately knows nothing about policy."""

    def __init__(self, known_surfaces: Iterable[str]) -> None:
        surface_ids = sorted(set(known_surfaces))
        if not surface_ids:
            raise ValueError("known_surfaces must not be empty")
        self._stores: Dict[str, Dict[str, Any]] = {surface: {} for surface in surface_ids}
        self._journal: list[dict[str, str]] = []

    def port(self) -> "EffectPort":
        return EffectPort(self)

    def snapshot(self) -> Snapshot:
        return {
            surface: {
                key: canonical_sha256(value)
                for key, value in sorted(values.items())
            }
            for surface, values in sorted(self._stores.items())
        }

    def journal(self) -> tuple[Mapping[str, str], ...]:
        return tuple(dict(item) for item in self._journal)

    def _emit(self, surface: str, key: str, value: Any) -> None:
        if not isinstance(surface, str) or not surface:
            raise ValueError("effect surface must be a non-empty string")
        if not isinstance(key, str) or not key:
            raise ValueError("effect key must be a non-empty string")
        # Validate and digest before mutating state. A rejected value must not
        # leave a partially applied write that later breaks snapshotting.
        value_sha256 = canonical_sha256(value)
        # Unknown surfaces are intentionally retained.  The runner classifies
        # their snapshot changes as undeclared effects instead of converting a
        # potentially real bypass into an adapter exception/inconclusive run.
        self._stores.setdefault(surface, {})
        self._stores[surface][key] = value
        self._journal.append(
            {
                "surface": surface,
                "key": key,
                "value_sha256": value_sha256,
            }
        )


class EffectPort:
    """A dumb effect port: it applies writes and performs no authorization."""

    def __init__(self, world: SyntheticWorld) -> None:
        self._world = world

    def emit(self, surface: str, key: str, value: Any) -> None:
        self._world._emit(surface, key, value)


def observe_surface_changes(before: Snapshot, after: Snapshot) -> tuple[SurfaceChange, ...]:
    """Observe state changes using snapshots only; no decision input is accepted."""

    changes: list[SurfaceChange] = []
    for surface in sorted(set(before) | set(after)):
        before_entries = before.get(surface, {})
        after_entries = after.get(surface, {})
        for key in sorted(set(before_entries) | set(after_entries)):
            old = before_entries.get(key)
            new = after_entries.get(key)
            if old == new:
                continue
            if old is None:
                kind = "ADDED"
            elif new is None:
                kind = "DELETED"
            else:
                kind = "MODIFIED"
            changes.append(SurfaceChange(surface, key, kind, old, new))
    return tuple(changes)
