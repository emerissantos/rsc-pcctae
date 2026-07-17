from __future__ import annotations

from dataclasses import dataclass

from apps.contas.models import IdentidadeExterna, Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional


@dataclass(frozen=True)
class DadosFuncionaisUsuario:
    identidade: IdentidadeExterna | None
    pessoa: PessoaInstitucional | None
    servidor: Servidor | None
    vinculos: tuple[VinculoFuncional, ...]


def carregar_dados_funcionais(usuario: Usuario) -> DadosFuncionaisUsuario:
    identidades = list(
        usuario.identidades_externas.select_related("pessoa").order_by(
            "-ativo_na_origem",
            "-ultima_sincronizacao_em",
            "-updated_at",
        )
    )
    identidade = next((item for item in identidades if item.pessoa_id), None)
    if identidade is None and identidades:
        identidade = identidades[0]

    pessoa = identidade.pessoa if identidade and identidade.pessoa_id else None
    servidor = None
    if pessoa is not None:
        try:
            servidor = pessoa.servidor
        except Servidor.DoesNotExist:
            servidor = None

    vinculos: tuple[VinculoFuncional, ...] = ()
    if servidor is not None:
        vinculos = tuple(
            servidor.vinculos.all().order_by(
                "-ativo",
                "siape",
                "id_servidor_externo",
            )
        )

    return DadosFuncionaisUsuario(
        identidade=identidade,
        pessoa=pessoa,
        servidor=servidor,
        vinculos=vinculos,
    )
