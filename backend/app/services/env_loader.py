"""Lightweight local environment loader.

This intentionally avoids adding a dependency. It loads `.env` and `.env.local`
from the repo root so CLI tools such as Claude Code or Codex can receive local
OAuth/API environment variables without hardcoding secrets in the repo.
"""

from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = (REPO_ROOT / ".env", REPO_ROOT / ".env.local")


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip()

    if not key:
        return None

    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    return key, value


def load_local_env() -> dict[str, str]:
    """Return process env plus values from `.env` and `.env.local`.

    Existing process variables win over file variables. This prevents a shell or
    service manager from being accidentally overridden.
    """

    env = dict(os.environ)
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(line)
            if not parsed:
                continue
            key, value = parsed
            env.setdefault(key, value)
    return env
