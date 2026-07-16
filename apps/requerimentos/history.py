from __future__ import annotations

from django.db.models import Prefetch

from apps.triagem.models import TriagemRequerimento, VerificacaoChecklistTriagem

from .models import Requerimento


def montar_contexto_historico(
    requerimento: Requerimento,
    *,
    incluir_triagens_em_andamento: bool = False,
) -> dict:
    """Carrega a memória do processo sem expor rascunhos ao requerente."""
    verificacoes = VerificacaoChecklistTriagem.objects.select_related(
        "item", "created_by", "updated_by"
    ).order_by("item__ordem", "item_codigo_snapshot")

    triagens_qs = requerimento.triagens.select_related(
        "responsavel", "created_by", "updated_by"
    ).prefetch_related(
        Prefetch(
            "verificacoes",
            queryset=verificacoes,
            to_attr="verificacoes_historico",
        )
    )
    if not incluir_triagens_em_andamento:
        triagens_qs = triagens_qs.exclude(
            resultado=TriagemRequerimento.Resultado.EM_ANDAMENTO
        )

    triagens = list(triagens_qs.order_by("-rodada"))
    for indice, triagem in enumerate(triagens):
        triagem.eh_ultima_historico = indice == 0
        triagem.avaliador_conclusao = triagem.updated_by or triagem.responsavel
        triagem.pendencias_historico = [
            verificacao
            for verificacao in triagem.verificacoes_historico
            if verificacao.situacao
            == VerificacaoChecklistTriagem.Situacao.NAO_CONFORME
        ]

    rotulos_situacao = dict(Requerimento.Situacao.choices)
    movimentacoes = list(
        requerimento.historico.select_related("created_by").order_by("-created_at")
    )
    for movimentacao in movimentacoes:
        movimentacao.situacao_anterior_label = rotulos_situacao.get(
            movimentacao.situacao_anterior,
            movimentacao.situacao_anterior,
        )
        movimentacao.situacao_nova_label = rotulos_situacao.get(
            movimentacao.situacao_nova,
            movimentacao.situacao_nova,
        )

    return {
        "triagens_historico": triagens,
        "movimentacoes_historico": movimentacoes,
        "ultima_triagem_historico": triagens[0] if triagens else None,
    }
