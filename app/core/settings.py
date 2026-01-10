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
    app_name: str
    environment: str
    debug: bool
    database_url: str
    db_echo: bool
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


def _settings_from_env() -> dict[str, object]:
    return {
        "app_name": os.getenv("APP_NAME", "SunuPass"),
        "environment": os.getenv("ENVIRONMENT", "local"),
        "debug": os.getenv("DEBUG", "false").strip().lower() == "true",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./app.db"),
        "db_echo": os.getenv("DB_ECHO", "false").strip().lower() == "true",
        "jwt_secret_key": os.getenv("JWT_SECRET_KEY", "CHANGE_ME"),
        "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env_file = os.getenv("ENV_FILE", ".env")
    _load_env_file(Path(env_file))
    return Settings(**_settings_from_env())
