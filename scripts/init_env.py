#!/usr/bin/env python3
"""Cria um .env local com segredos aleatórios sem sobrescrever arquivo existente."""

from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / ".env.example"
TARGET = ROOT / ".env"


def main() -> None:
    if TARGET.exists():
        raise SystemExit("O arquivo .env já existe; nenhuma alteração foi realizada.")
    content = EXAMPLE.read_text(encoding="utf-8")
    content = content.replace(
        "GERE-UMA-CHAVE-ALEATORIA-FORTE",
        secrets.token_urlsafe(64),
    )
    content = content.replace(
        "DEFINA-UMA-SENHA-LOCAL",
        secrets.token_urlsafe(32),
    )
    TARGET.write_text(content, encoding="utf-8")
    TARGET.chmod(0o600)
    print("Arquivo .env criado com permissão 0600.")
    print("Preencha os client IDs, client secrets e a x-api-key da UFSB.")


if __name__ == "__main__":
    main()
