from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.integracoes.common.exceptions import IntegrationInvalidResponseError

from .schemas import ServidorInstitucionalDTO, UsuarioInstitucionalDTO


def _required(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value in (None, ""):
        raise IntegrationInvalidResponseError(f"Campo obrigatório ausente na API: {key}")
    return value


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise IntegrationInvalidResponseError("A API retornou um identificador inválido.") from exc


def _to_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "sim", "yes", "ativo"}


def _timestamp_ms_to_date(value: Any):
    if value in (None, ""):
        return None
    try:
        timestamp = float(value) / 1000
        return datetime.fromtimestamp(timestamp, tz=UTC).date()
    except (TypeError, ValueError, OSError, OverflowError) as exc:
        raise IntegrationInvalidResponseError("A API retornou data de admissão inválida.") from exc


def map_usuario(payload: dict[str, Any]) -> UsuarioInstitucionalDTO:
    return UsuarioInstitucionalDTO(
        id_institucional=int(_required(payload, "id-institucional")),
        id_usuario=int(_required(payload, "id-usuario")),
        id_unidade=_to_int(payload.get("id-unidade")),
        login=str(_required(payload, "login")).strip(),
        nome_pessoa=str(_required(payload, "nome-pessoa")).strip(),
        cpf_cnpj=_to_str(payload.get("cpf-cnpj")),
        ativo=_to_bool(payload.get("ativo")),
        email=_to_str(payload.get("email")),
        id_foto=_to_int(payload.get("id-foto")),
        chave_foto=_to_str(payload.get("chave-foto")),
        url_foto=_to_str(payload.get("url-foto")),
    )


def map_servidor(payload: dict[str, Any]) -> ServidorInstitucionalDTO:
    return ServidorInstitucionalDTO(
        id_servidor=int(_required(payload, "id-servidor")),
        id_institucional=int(_required(payload, "id-institucional")),
        nome=str(_required(payload, "nome")).strip(),
        nome_identificacao=_to_str(payload.get("nome-identificacao")),
        email=_to_str(payload.get("email")),
        # A conversão para string preserva o valor recebido. Zeros já perdidos por
        # serialização numérica na origem não são recompostos por suposição.
        siape=str(_required(payload, "siape")).strip(),
        digito_siape=_to_str(payload.get("digito-siape")),
        id_ativo=_to_int(payload.get("id-ativo")),
        id_situacao=_to_int(payload.get("id-situacao")),
        id_categoria=_to_int(payload.get("id-categoria")),
        id_lotacao=_to_int(payload.get("id-lotacao")),
        lotacao=_to_str(payload.get("lotacao")),
        id_unidade_exercicio=_to_int(payload.get("id-unidade-exercicio")),
        unidade_exercicio=_to_str(payload.get("unidade-exercicio")),
        id_cargo=_to_int(payload.get("id-cargo")),
        cargo=_to_str(payload.get("cargo")),
        id_tipo_formacao=_to_int(payload.get("id-tipo-formacao")),
        regime_trabalho=_to_int(payload.get("regime-trabalho")),
        data_admissao=_timestamp_ms_to_date(payload.get("data-admissao")),
        ativo=_to_bool(payload.get("ativo")),
    )
