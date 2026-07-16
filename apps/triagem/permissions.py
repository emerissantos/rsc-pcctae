from __future__ import annotations

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.comissoes.models import Comissao

PERMISSAO_ACESSAR_FILA = "triagem.acessar_fila_triagem"
PERMISSAO_INICIAR = "triagem.iniciar_triagem"
PERMISSAO_ALTERAR = "triagem.alterar_triagem"
PERMISSAO_CONCLUIR = "triagem.concluir_triagem"


def comissoes_ativas_do_usuario(usuario) -> QuerySet[Comissao]:
    """Comissões vigentes nas quais o usuário possui participação ativa."""
    if not getattr(usuario, "is_authenticated", False):
        return Comissao.objects.none()

    hoje = timezone.localdate()
    return (
        Comissao.objects.filter(
            ativa=True,
            inicio_vigencia__lte=hoje,
            membros__usuario=usuario,
            membros__ativo=True,
            membros__inicio_mandato__lte=hoje,
        )
        .filter(Q(fim_vigencia__isnull=True) | Q(fim_vigencia__gte=hoje))
        .filter(Q(membros__fim_mandato__isnull=True) | Q(membros__fim_mandato__gte=hoje))
        .distinct()
    )


def possui_participacao_ativa(usuario, *, comissao_id=None) -> bool:
    queryset = comissoes_ativas_do_usuario(usuario)
    if comissao_id is not None:
        queryset = queryset.filter(pk=comissao_id)
    return queryset.exists()


def possui_permissao_operacional(usuario, permissao: str) -> bool:
    """Permissões explícitas nunca são inferidas de ``is_staff``."""
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True
    return usuario.has_perm(PERMISSAO_ACESSAR_FILA) and usuario.has_perm(permissao)


def pode_acessar_fila(usuario) -> bool:
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser or usuario.has_perm(PERMISSAO_ACESSAR_FILA):
        return True
    return possui_participacao_ativa(usuario)


def pode_visualizar_requerimento(usuario, requerimento) -> bool:
    if not getattr(usuario, "is_authenticated", False) or not requerimento.comissao_id:
        return False
    if usuario.is_superuser or usuario.has_perm(PERMISSAO_ACESSAR_FILA):
        return True
    return possui_participacao_ativa(usuario, comissao_id=requerimento.comissao_id)


def pode_iniciar_triagem(usuario, requerimento) -> bool:
    if requerimento.comissao_id and possui_participacao_ativa(
        usuario, comissao_id=requerimento.comissao_id
    ):
        return True
    return possui_permissao_operacional(usuario, PERMISSAO_INICIAR)


def pode_alterar_triagem(usuario, requerimento) -> bool:
    if requerimento.comissao_id and possui_participacao_ativa(
        usuario, comissao_id=requerimento.comissao_id
    ):
        return True
    return possui_permissao_operacional(usuario, PERMISSAO_ALTERAR)


def pode_concluir_triagem(usuario, requerimento) -> bool:
    if requerimento.comissao_id and possui_participacao_ativa(
        usuario, comissao_id=requerimento.comissao_id
    ):
        return True
    return possui_permissao_operacional(usuario, PERMISSAO_CONCLUIR)
