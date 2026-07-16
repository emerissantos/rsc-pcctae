from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.comissoes.models import Comissao
from apps.requerimentos.models import HistoricoRequerimento, Requerimento

from .forms import TriagemConclusaoForm, VerificacaoChecklistForm
from .models import (
    ConfiguracaoTriagem,
    ItemChecklistTriagem,
    TriagemRequerimento,
    VerificacaoChecklistTriagem,
)
from .permissions import (
    PERMISSAO_ACESSAR_FILA,
    comissoes_ativas_do_usuario,
    pode_acessar_fila,
    pode_alterar_triagem,
    pode_concluir_triagem,
    pode_iniciar_triagem,
    pode_visualizar_requerimento,
)


def _comissao_atual():
    hoje = timezone.localdate()
    return (
        Comissao.objects.filter(ativa=True, inicio_vigencia__lte=hoje)
        .filter(Q(fim_vigencia__isnull=True) | Q(fim_vigencia__gte=hoje))
        .order_by("-inicio_vigencia", "-pk")
        .first()
    )


def _obter_requerimento(uuid) -> Requerimento:
    return get_object_or_404(
        Requerimento.objects.select_related(
            "requerente", "vinculo", "vinculo__servidor", "nivel_pretendido", "comissao"
        ),
        uuid=uuid,
    )


def _processar_formularios_triagem(request, triagem: TriagemRequerimento) -> bool:
    """Persiste o checklist e a orientação; retorna True quando tudo é válido."""
    valido = True
    for verificacao in triagem.verificacoes.select_related("item"):
        form = VerificacaoChecklistForm(
            request.POST,
            instance=verificacao,
            prefix=str(verificacao.uuid),
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
        else:
            valido = False
            for mensagens_campo in form.errors.values():
                for mensagem in mensagens_campo:
                    messages.error(request, f"{verificacao.item.codigo}: {mensagem}")

    form_triagem = TriagemConclusaoForm(request.POST, instance=triagem)
    if form_triagem.is_valid():
        obj = form_triagem.save(commit=False)
        obj.updated_by = request.user
        obj.save(update_fields=["orientacao_correcao", "updated_by", "updated_at"])
    else:
        valido = False
        for mensagens_campo in form_triagem.errors.values():
            for mensagem in mensagens_campo:
                messages.error(request, mensagem)
    return valido


@login_required
def fila(request):
    situacoes = [
        Requerimento.Situacao.SUBMETIDO,
        Requerimento.Situacao.EM_TRIAGEM,
        Requerimento.Situacao.PENDENTE_CORRECAO,
        Requerimento.Situacao.EM_ANALISE,
    ]
    queryset = Requerimento.objects.filter(situacao__in=situacoes).select_related(
        "requerente", "vinculo", "nivel_pretendido", "comissao"
    )
    if not pode_acessar_fila(request.user):
        raise PermissionDenied
    if not (request.user.is_superuser or request.user.has_perm(PERMISSAO_ACESSAR_FILA)):
        queryset = queryset.filter(comissao__in=comissoes_ativas_do_usuario(request.user))
    return render(request, "triagem/fila.html", {"requerimentos": queryset})


@login_required
@require_POST
@transaction.atomic
def iniciar(request, uuid):
    requerimento = _obter_requerimento(uuid)
    if requerimento.situacao != Requerimento.Situacao.SUBMETIDO:
        messages.error(request, "Somente requerimentos submetidos podem iniciar uma triagem.")
        return redirect("triagem:fila")

    if not requerimento.comissao_id:
        if request.user.is_superuser or request.user.has_perm(PERMISSAO_ACESSAR_FILA):
            comissao = _comissao_atual()
        else:
            comissao = (
                comissoes_ativas_do_usuario(request.user).order_by("-inicio_vigencia").first()
            )
        if not comissao:
            messages.error(request, "Não há comissão vigente disponível para a triagem.")
            return redirect("triagem:fila")
        requerimento.comissao = comissao

    if not pode_iniciar_triagem(request.user, requerimento):
        raise PermissionDenied

    rodada = (requerimento.triagens.aggregate(maior=Max("rodada"))["maior"] or 0) + 1
    itens = list(ItemChecklistTriagem.objects.filter(ativo=True))
    if not itens:
        messages.error(
            request,
            "O checklist de triagem ainda não foi configurado. "
            "Execute a seed ou cadastre os itens.",
        )
        return redirect("triagem:fila")

    triagem = TriagemRequerimento.objects.create(
        requerimento=requerimento,
        rodada=rodada,
        responsavel=request.user,
        created_by=request.user,
        updated_by=request.user,
    )
    VerificacaoChecklistTriagem.objects.bulk_create(
        [
            VerificacaoChecklistTriagem(
                triagem=triagem,
                item=item,
                item_codigo_snapshot=item.codigo,
                item_titulo_snapshot=item.titulo,
                item_descricao_snapshot=item.descricao,
                item_obrigatorio_snapshot=item.obrigatorio,
                item_confere_comprovantes_snapshot=item.confere_comprovantes,
                created_by=request.user,
                updated_by=request.user,
            )
            for item in itens
        ]
    )
    situacao_anterior = requerimento.situacao
    requerimento.situacao = Requerimento.Situacao.EM_TRIAGEM
    requerimento.updated_by = request.user
    requerimento.save(update_fields=["comissao", "situacao", "updated_by", "updated_at"])
    HistoricoRequerimento.objects.create(
        requerimento=requerimento,
        situacao_anterior=situacao_anterior,
        situacao_nova=Requerimento.Situacao.EM_TRIAGEM,
        descricao=f"Triagem documental iniciada — rodada {rodada}.",
        created_by=request.user,
        updated_by=request.user,
    )
    messages.success(request, "Triagem iniciada.")
    return redirect("triagem:detalhe", uuid=triagem.uuid)


@login_required
def detalhe(request, uuid):
    triagem = get_object_or_404(
        TriagemRequerimento.objects.select_related(
            "requerimento",
            "requerimento__requerente",
            "requerimento__vinculo",
            "requerimento__nivel_pretendido",
            "requerimento__comissao",
            "responsavel",
        ).prefetch_related("verificacoes__item"),
        uuid=uuid,
    )
    if not pode_visualizar_requerimento(request.user, triagem.requerimento):
        raise PermissionDenied
    formularios = [
        (verificacao, VerificacaoChecklistForm(instance=verificacao, prefix=str(verificacao.uuid)))
        for verificacao in triagem.verificacoes.all()
    ]
    conclusao_form = TriagemConclusaoForm(instance=triagem)
    lancamentos = triagem.requerimento.lancamentos.select_related(
        "item__requisito"
    ).prefetch_related("documentos")
    return render(
        request,
        "triagem/detalhe.html",
        {
            "triagem": triagem,
            "formularios": formularios,
            "conclusao_form": conclusao_form,
            "lancamentos": lancamentos,
        },
    )


@login_required
@require_POST
@transaction.atomic
def salvar(request, uuid):
    triagem = get_object_or_404(
        TriagemRequerimento.objects.select_related("requerimento"),
        uuid=uuid,
    )
    if not pode_alterar_triagem(request.user, triagem.requerimento):
        raise PermissionDenied
    if not triagem.em_andamento:
        messages.error(request, "Esta triagem já foi concluída.")
        return redirect("triagem:detalhe", uuid=triagem.uuid)

    if _processar_formularios_triagem(request, triagem):
        messages.success(request, "Triagem salva.")
    return redirect("triagem:detalhe", uuid=triagem.uuid)


@login_required
@require_POST
@transaction.atomic
def concluir(request, uuid):
    triagem = get_object_or_404(
        TriagemRequerimento.objects.select_for_update().select_related("requerimento"),
        uuid=uuid,
    )
    if not pode_concluir_triagem(request.user, triagem.requerimento):
        raise PermissionDenied
    if not triagem.em_andamento:
        messages.error(request, "Esta triagem já foi concluída.")
        return redirect("triagem:detalhe", uuid=triagem.uuid)

    # Persiste os campos apresentados na mesma tela antes de validar a conclusão.
    if not _processar_formularios_triagem(request, triagem):
        return redirect("triagem:detalhe", uuid=triagem.uuid)
    triagem.refresh_from_db()
    erros = triagem.validar_conclusao()
    if erros:
        for erro in erros:
            messages.error(request, erro)
        return redirect("triagem:detalhe", uuid=triagem.uuid)

    requerimento = triagem.requerimento
    situacao_anterior = requerimento.situacao
    triagem.concluida_em = timezone.now()
    triagem.updated_by = request.user

    if triagem.possui_pendencia:
        configuracao = ConfiguracaoTriagem.carregar()
        triagem.resultado = TriagemRequerimento.Resultado.PENDENCIA
        triagem.calcular_prazo_correcao(configuracao.prazo_correcao_dias)
        requerimento.situacao = Requerimento.Situacao.PENDENTE_CORRECAO
        descricao = (
            f"Triagem concluída com pendências. Prazo para correção até "
            f"{triagem.prazo_correcao_ate:%d/%m/%Y}."
        )
    else:
        triagem.resultado = TriagemRequerimento.Resultado.APTO
        requerimento.situacao = Requerimento.Situacao.EM_ANALISE
        descricao = "Triagem concluída sem pendências; requerimento encaminhado para análise."

    triagem.save(
        update_fields=[
            "resultado",
            "concluida_em",
            "prazo_correcao_dias_snapshot",
            "prazo_correcao_ate",
            "updated_by",
            "updated_at",
        ]
    )
    requerimento.updated_by = request.user
    requerimento.save(update_fields=["situacao", "updated_by", "updated_at"])
    HistoricoRequerimento.objects.create(
        requerimento=requerimento,
        situacao_anterior=situacao_anterior,
        situacao_nova=requerimento.situacao,
        descricao=descricao,
        created_by=request.user,
        updated_by=request.user,
    )
    messages.success(request, descricao)
    return redirect("triagem:fila")
