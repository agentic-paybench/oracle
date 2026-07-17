"""Load and validate the shared regulatory_posture PDP config (ADR-009).

The oracle repo OWNS these two files at repo-root ``config/``. Fail-closed: a
missing or malformed config must never yield an emit (see :func:`load_config`).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from pdp.posture import Posture
from pdp.gates import is_open

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = _REPO_ROOT / "config"


class ConfigError(ValueError):
    """Raised when a posture config is missing or malformed. Fail-closed."""


@dataclass(frozen=True)
class PostureConfig:
    config_id: str
    posture: Posture
    gates: dict  # gate key -> "open" | "closed"
    audit: dict

    def gate_open(self, key: str) -> bool:
        return is_open(self.gates, key)

    def is_testnet(self) -> bool:
        """config_id is the deployment discriminator (testnet demo vs live public)."""
        return self.config_id == "testnet"


def _config_dir() -> Path:
    override = os.environ.get("ORACLE_POSTURE_CONFIG")
    return Path(override) if override else DEFAULT_CONFIG_DIR


def load_config(path) -> PostureConfig:
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"posture config not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"posture config not valid JSON: {p}: {e}") from e
    try:
        posture = Posture[data["regulatory_posture"]]
    except (KeyError, TypeError) as e:
        raise ConfigError(f"unknown/missing regulatory_posture in {p}") from e
    gates = data.get("gates")
    if not isinstance(gates, dict):
        raise ConfigError(f"missing gates map in {p}")
    for key, value in gates.items():
        if value not in ("open", "closed"):
            raise ConfigError(f"gate {key} has invalid value {value!r} in {p}")
    return PostureConfig(
        config_id=str(data.get("config_id", p.stem)),
        posture=posture,
        gates=dict(gates),
        audit=dict(data.get("audit", {})),
    )


def load_named(name: str) -> PostureConfig:
    """Load ``config/regulatory_posture.<name>.json`` (name in {"testnet","live"})."""
    return load_config(_config_dir() / f"regulatory_posture.{name}.json")
