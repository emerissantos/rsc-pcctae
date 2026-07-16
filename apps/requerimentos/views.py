from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.pontuacao.models import ItemPontuacao, Requisito

from .forms import RequerimentoForm, limpar_quantidade
from .models import DocumentoLancamento, LancamentoItem, Requerimento


def _requerimento_do_usuario(request, uuid, *, editavel=False) -> Requerimento:
    queryset = Requerimento.objects.select_related(
        "requerente", "vinculo", "vinculo__servidor", "nivel_pretendido", "comissao"
    )
    requerimento = get_object_or_404(queryset, uuid=uuid)
    if not request.user.is_staff and requerimento.requerente_id != request.user.id:
        raise PermissionDenied
    if editavel and not requerimento.pode_editar:
        raise PermissionDenied("O requerimento não está disponível para edição.")
    return requerimento


def _validar_upload(upload) -> None:
    if upload.size > settings.RSC_MAX_UPLOAD_BYTES:
        raise ValidationError("O arquivo excede o limite permitido.")
    extensao = Path(upload.name).suffix.lower().lstrip(".")
    permitidas = {item.lower() for item in settings.RSC_ALLOWED_UPLOAD_EXTENSIONS}
    if permitidas and extensao not in permitidas:
        raise ValidationError(f"A extensão .{extensao} não é permitida.")
    tipo = getattr(upload, "content_type", "") or ""
    tipos = {item.lower() for item in settings.RSC_ALLOWED_UPLOAD_MIME_TYPES}
    if tipos and tipo.lower() not in tipos:
        raise ValidationError("O tipo do arquivo não é permitido.")


@login_required
def lista(request):
    queryset = Requerimento.objects.select_related("vinculo", "nivel_pretendido", "requerente")
    if not request.user.is_staff:
        queryset = queryset.filter(requerente=request.user)
    return render(request, "requerimentos/lista.html", {"requerimentos": queryset})


@login_required
def criar(request):
    if request.method == "POST":
        form = RequerimentoForm(request.POST, usuario=request.user)
        if form.is_valid():
            requerimento = form.save(commit=False)
            requerimento.requerente = request.user
            requerimento.created_by = request.user
            requerimento.updated_by = request.user
            requerimento.save()
            messages.success(request, "Requerimento criado. Agora informe os itens de pontuação.")
            return redirect("requerimentos:itens", uuid=requerimento.uuid)
    else:
        form = RequerimentoForm(usuario=request.user)
    return render(request, "requerimentos/criar.html", {"form": form})


@login_required
def detalhe(request, uuid):
    requerimento = _requerimento_do_usuario(request, uuid)
    lancamentos = requerimento.lancamentos.select_related(
        "item__requisito"
    ).prefetch_related("documentos")
    return render(
        request,
        "requerimentos/detalhe.html",
        {"requerimento": requerimento, "lancamentos": lancamentos},
    )


@login_required
def itens(request, uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    requisitos = Requisito.objects.filter(ativo=True).prefetch_related("itens")
    lancamentos = {
        lancamento.item_id: lancamento
        for lancamento in requerimento.lancamentos.prefetch_related("documentos")
    }
    for requisito in requisitos:
        for item in requisito.itens.all():
            item.lancamento_atual = lancamentos.get(item.id)
    return render(
        request,
        "requerimentos/itens.html",
        {"requerimento": requerimento, "requisitos": requisitos},
    )


@login_required
@require_POST
@transaction.atomic
def salvar_item(request, uuid, item_uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    item = get_object_or_404(ItemPontuacao, uuid=item_uuid, ativo=True)
    try:
        quantidade = limpar_quantidade(request.POST.get("quantidade", ""))
        item.calcular(quantidade)
    except ValidationError as exc:
        mensagem = exc.messages[0]
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "erro": mensagem}, status=400)
        messages.error(request, mensagem)
        return redirect("requerimentos:itens", uuid=requerimento.uuid)

    lancamento, created = LancamentoItem.objects.get_or_create(
        requerimento=requerimento,
        item=item,
        defaults={
            "quantidade_declarada": quantidade,
            "observacao": request.POST.get("observacao", "").strip(),
            "created_by": request.user,
            "updated_by": request.user,
        },
    )
    if not created:
        lancamento.quantidade_declarada = quantidade
        lancamento.observacao = request.POST.get("observacao", "").strip()
        lancamento.updated_by = request.user
        lancamento.save()

    erros_upload = []
    for upload in request.FILES.getlist("documentos"):
        try:
            _validar_upload(upload)
            DocumentoLancamento.objects.create(
                lancamento=lancamento,
                arquivo=upload,
                nome_original=upload.name,
                tipo_mime=getattr(upload, "content_type", "") or "",
                tamanho_bytes=upload.size,
                created_by=request.user,
                updated_by=request.user,
            )
        except ValidationError as exc:
            erros_upload.extend(exc.messages)

    requerimento.refresh_from_db(fields=["pontuacao_declarada"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "pontuacao_item": f"{lancamento.pontuacao_declarada:.2f}",
                "pontuacao_total": f"{requerimento.pontuacao_declarada:.2f}",
                "documentos": lancamento.documentos.filter(ativo=True).count(),
                "avisos": erros_upload,
            }
        )
    messages.success(request, f"Item {item.codigo} salvo.")
    for erro in erros_upload:
        messages.warning(request, erro)
    return redirect("requerimentos:itens", uuid=requerimento.uuid)


@login_required
@require_POST
def remover_item(request, uuid, item_uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    lancamento = get_object_or_404(
        LancamentoItem,
        requerimento=requerimento,
        item__uuid=item_uuid,
    )
    codigo = lancamento.item_codigo_snapshot
    lancamento.delete()
    messages.success(request, f"Item {codigo} removido.")
    return redirect("requerimentos:itens", uuid=requerimento.uuid)


@login_required
@require_POST
def remover_documento(request, uuid, documento_uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    documento = get_object_or_404(
        DocumentoLancamento,
        uuid=documento_uuid,
        lancamento__requerimento=requerimento,
    )
    documento.delete()
    messages.success(request, "Documento removido.")
    return redirect("requerimentos:itens", uuid=requerimento.uuid)


@login_required
def revisao(request, uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    lancamentos = requerimento.lancamentos.select_related(
        "item__requisito"
    ).prefetch_related("documentos")
    erros = requerimento.validar_submissao()
    return render(
        request,
        "requerimentos/revisao.html",
        {"requerimento": requerimento, "lancamentos": lancamentos, "erros": erros},
    )


@login_required
@require_POST
def submeter(request, uuid):
    requerimento = _requerimento_do_usuario(request, uuid, editavel=True)
    try:
        requerimento.submeter(request.user)
    except ValidationError as exc:
        for mensagem in exc.messages:
            messages.error(request, mensagem)
        return redirect("requerimentos:revisao", uuid=requerimento.uuid)
    messages.success(request, "Requerimento submetido com sucesso.")
    return redirect("requerimentos:detalhe", uuid=requerimento.uuid)
