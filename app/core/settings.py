from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if not key:
            continue
        if key in os.environ:
            continue
        os.environ[key] = value


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "SunuPass")
    environment: str = os.getenv("ENVIRONMENT", "local")
    debug: bool = os.getenv("DEBUG", "false").strip().lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env_file = os.getenv("ENV_FILE", ".env")
    _load_env_file(Path(env_file))
    return Settings()
