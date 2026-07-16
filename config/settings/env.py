import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

# O arquivo .env é útil no desenvolvimento e em instalações simples. Variáveis
# já presentes no ambiente sempre têm precedência (override=False).
if os.getenv("DJANGO_READ_DOT_ENV_FILE", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
    "sim",
}:
    load_dotenv(BASE_DIR / ".env", override=False)


def get_env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"A variável de ambiente obrigatória {name} não foi definida.")
    return value or ""


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def get_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]

