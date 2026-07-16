from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class UsuarioInstitucionalDTO:
    id_institucional: int
    id_usuario: int
    id_unidade: int | None
    login: str
    nome_pessoa: str
    cpf_cnpj: str | None
    ativo: bool
    email: str | None
    id_foto: int | None = None
    chave_foto: str | None = None
    url_foto: str | None = None


@dataclass(frozen=True, slots=True)
class ServidorInstitucionalDTO:
    id_servidor: int
    id_institucional: int
    nome: str
    nome_identificacao: str | None
    email: str | None
    siape: str
    digito_siape: str | None
    id_ativo: int | None
    id_situacao: int | None
    id_categoria: int | None
    id_lotacao: int | None
    lotacao: str | None
    id_unidade_exercicio: int | None
    unidade_exercicio: str | None
    id_cargo: int | None
    cargo: str | None
    id_tipo_formacao: int | None
    regime_trabalho: int | None
    data_admissao: date | None
    ativo: bool


@dataclass(frozen=True, slots=True)
class PageMetadata:
    pages: int | None
    total: int | None


@dataclass(frozen=True, slots=True)
class RateLimitMetadata:
    limit: int | None
    remaining: int | None
    reset_seconds: int | None


@dataclass(frozen=True, slots=True)
class APIResult:
    data: Any
    page: PageMetadata
    rate_limit: RateLimitMetadata
    status_code: int
