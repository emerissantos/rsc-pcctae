from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.integracoes.ufsb.api.schemas import (
    ServidorInstitucionalDTO,
    UsuarioInstitucionalDTO,
)

from ..models import ExecucaoSincronizacao, PessoaInstitucional, Servidor, VinculoFuncional


@dataclass(frozen=True, slots=True)
class SyncResult:
    pessoa: PessoaInstitucional
    servidor: Servidor | None
    vinculos: tuple[VinculoFuncional, ...]
    created_count: int
    updated_count: int


class PersistirCadastroInstitucionalService:
    """Persiste uma fotografia atual da API sem apagar vínculos históricos ausentes."""

    @classmethod
    @transaction.atomic
    def execute(
        cls,
        *,
        usuario_api: UsuarioInstitucionalDTO,
        servidores_api: list[ServidorInstitucionalDTO],
        correlation_id: str = "",
    ) -> SyncResult:
        now = timezone.now()
        created_count = 0
        updated_count = 0

        pessoa, pessoa_created = PessoaInstitucional.objects.update_or_create(
            id_institucional=usuario_api.id_institucional,
            defaults={
                "nome": usuario_api.nome_pessoa,
                "email_institucional": (usuario_api.email or "").lower(),
                "ativo_na_origem": usuario_api.ativo,
                "sincronizado_em": now,
            },
        )
        created_count += int(pessoa_created)
        updated_count += int(not pessoa_created)

        servidor = None
        vinculos: list[VinculoFuncional] = []
        if servidores_api:
            current = cls._select_current_server(servidores_api)
            servidor, servidor_created = Servidor.objects.update_or_create(
                pessoa=pessoa,
                defaults={
                    "nome_atual": current.nome,
                    "nome_identificacao_atual": current.nome_identificacao or "",
                    "email_atual": (current.email or usuario_api.email or "").lower(),
                    "ativo": any(item.ativo for item in servidores_api),
                    "ultima_sincronizacao_em": now,
                },
            )
            created_count += int(servidor_created)
            updated_count += int(not servidor_created)

            for item in servidores_api:
                vinculo, vinculo_created = VinculoFuncional.objects.update_or_create(
                    provedor_origem="ufsb_api",
                    id_servidor_externo=item.id_servidor,
                    defaults={
                        "servidor": servidor,
                        "siape": item.siape,
                        "digito_siape": item.digito_siape or "",
                        "id_ativo_externo": item.id_ativo,
                        "id_situacao_externa": item.id_situacao,
                        "id_categoria_externa": item.id_categoria,
                        "id_lotacao_externa": item.id_lotacao,
                        "lotacao_nome": item.lotacao or "",
                        "id_unidade_exercicio_externa": item.id_unidade_exercicio,
                        "unidade_exercicio_nome": item.unidade_exercicio or "",
                        "id_cargo_externo": item.id_cargo,
                        "cargo_nome": item.cargo or "",
                        "id_tipo_formacao_externo": item.id_tipo_formacao,
                        "regime_trabalho": item.regime_trabalho,
                        "data_admissao": item.data_admissao,
                        "ativo": item.ativo,
                        "ultima_sincronizacao_em": now,
                    },
                )
                vinculos.append(vinculo)
                created_count += int(vinculo_created)
                updated_count += int(not vinculo_created)

        ExecucaoSincronizacao.objects.create(
            tipo=ExecucaoSincronizacao.Tipo.COMPLETA,
            pessoa=pessoa,
            id_institucional_consultado=usuario_api.id_institucional,
            iniciada_em=now,
            concluida_em=timezone.now(),
            situacao=ExecucaoSincronizacao.Situacao.CONCLUIDA,
            quantidade_recebida=1 + len(servidores_api),
            quantidade_criada=created_count,
            quantidade_atualizada=updated_count,
            identificador_correlacao=correlation_id,
        )
        return SyncResult(
            pessoa=pessoa,
            servidor=servidor,
            vinculos=tuple(vinculos),
            created_count=created_count,
            updated_count=updated_count,
        )

    @staticmethod
    def _select_current_server(
        servidores: list[ServidorInstitucionalDTO],
    ) -> ServidorInstitucionalDTO:
        active = [item for item in servidores if item.ativo]
        candidates = active or servidores
        return sorted(candidates, key=lambda item: item.id_servidor)[-1]
