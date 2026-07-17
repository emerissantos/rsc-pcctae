from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import (
    pretty_json,
    registrar_evento,
    registrar_mudanca,
    snapshot_model,
)
from apps.contas.models import Usuario
from apps.contas.permissions import (
    pode_importar_usuario_sig,
    usuario_pode_ser_simulado,
)
from apps.contas.services import ImportarUsuarioSIGService
from apps.integracoes.common.exceptions import IntegrationError

from .forms import ImportarUsuarioSIGForm
from .permissions import pode_acao, recursos_visiveis
from .registry import (
    AREAS,
    CadastroConfig,
    Filter,
    format_value,
    get_area,
    get_resource,
    resolve_value,
)

PER_PAGE_OPTIONS = (10, 25, 50, 100)


def _resource_or_404(slug: str) -> CadastroConfig:
    try:
        return get_resource(slug)
    except LookupError as exc:
        raise Http404 from exc


def _area_or_404(slug: str):
    try:
        return get_area(slug)
    except LookupError as exc:
        raise Http404 from exc


def _require_permission(request, resource: CadastroConfig, action: str) -> None:
    if not pode_acao(request.user, resource, action):
        raise PermissionDenied


def _object_identifier(obj) -> str:
    return str(getattr(obj, "uuid", obj.pk))


def _get_object(resource: CadastroConfig, object_id: str):
    if hasattr(resource.model, "uuid"):
        return get_object_or_404(resource.model, uuid=object_id)
    return get_object_or_404(resource.model, pk=object_id)


def _apply_search(queryset, resource: CadastroConfig, query: str):
    if not query or not resource.search_fields:
        return queryset
    condition = Q()
    for field in resource.search_fields:
        lookup = (
            field
            if "__" in field
            and field.split("__")[-1]
            in {
                "icontains",
                "iexact",
            }
            else f"{field}__icontains"
        )
        condition |= Q(**{lookup: query})
    return queryset.filter(condition).distinct()


def _filter_options(resource: CadastroConfig, spec: Filter):
    if spec.choices:
        return spec.choices
    field_name = spec.lookup.split("__", 1)[0]
    field = resource.model._meta.get_field(field_name)
    if spec.kind == "boolean":
        return (("1", "Sim"), ("0", "Não"))
    if spec.kind == "choices" or getattr(field, "choices", None):
        return tuple((str(value), str(label)) for value, label in field.choices)
    if spec.kind == "foreign" and getattr(field, "related_model", None):
        return tuple(
            (str(obj.pk), str(obj))
            for obj in field.related_model.objects.all().order_by(
                *field.related_model._meta.ordering
            )[:500]
        )
    return ()


def _apply_filters(queryset, resource: CadastroConfig, params):
    for spec in resource.filters:
        value = params.get(spec.param, "").strip()
        if value == "":
            continue
        if spec.kind == "boolean":
            value = value == "1"
        queryset = queryset.filter(**{spec.lookup: value})
    return queryset.distinct()


def _ordering_map(resource: CadastroConfig) -> dict[str, str]:
    return {column.key: column.ordering for column in resource.columns if column.ordering}


def _apply_ordering(queryset, resource: CadastroConfig, raw_ordering: str):
    allowed = _ordering_map(resource)
    descending = raw_ordering.startswith("-")
    key = raw_ordering.lstrip("-")
    field = allowed.get(key)
    if not field:
        return queryset.order_by(resource.default_ordering)
    return queryset.order_by(f"-{field}" if descending else field)


def _base_queryset(resource: CadastroConfig):
    queryset = resource.model.objects.all()
    if resource.select_related:
        queryset = queryset.select_related(*resource.select_related)
    if resource.prefetch_related:
        queryset = queryset.prefetch_related(*resource.prefetch_related)
    return queryset


def _build_rows(request, resource: CadastroConfig, objects):
    can_change = pode_acao(request.user, resource, "change") and resource.allow_update
    can_delete = pode_acao(request.user, resource, "delete") and resource.allow_delete
    rows = []
    for obj in objects:
        cells = []
        for column in resource.columns:
            formatted = format_value(resolve_value(obj, column.accessor), column.kind)
            formatted["css_class"] = column.css_class or column.kind
            cells.append(formatted)
        identifier = _object_identifier(obj)
        ator = getattr(request, "real_user", request.user)
        impersonate_url = ""
        if resource.slug == "usuarios" and usuario_pode_ser_simulado(ator, obj):
            impersonate_url = reverse(
                "contas:impersonar-iniciar",
                kwargs={"usuario_uuid": obj.uuid},
            )
        view_url = ""
        if resource.slug == "eventos-auditoria":
            view_url = reverse("cadastros:evento-auditoria-detalhe", kwargs={"uuid": obj.uuid})
        rows.append(
            {
                "object": obj,
                "cells": cells,
                "view_url": view_url,
                "edit_url": reverse(
                    "cadastros:editar",
                    kwargs={"resource_slug": resource.slug, "object_id": identifier},
                )
                if can_change
                else "",
                "delete_url": reverse(
                    "cadastros:excluir",
                    kwargs={"resource_slug": resource.slug, "object_id": identifier},
                )
                if can_delete
                else "",
                "impersonate_url": impersonate_url,
            }
        )
    return rows


def _query_string(params, **updates) -> str:
    query = params.copy()
    query.pop("partial", None)
    for key, value in updates.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()


@login_required
def central(request):
    cards = []
    for area in AREAS.values():
        visible = recursos_visiveis(request.user, area)
        if visible:
            cards.append({"area": area, "quantidade": len(visible)})
    if not cards:
        raise PermissionDenied
    return render(request, "cadastros/central.html", {"areas": cards})


@login_required
def area(request, area_slug):
    cadastro_area = _area_or_404(area_slug)
    resources = recursos_visiveis(request.user, cadastro_area)
    if not resources:
        raise PermissionDenied
    return render(
        request,
        "cadastros/area.html",
        {"area": cadastro_area, "resources": resources},
    )


@login_required
def lista(request, resource_slug):
    resource = _resource_or_404(resource_slug)
    _require_permission(request, resource, "view")

    query = request.GET.get("q", "").strip()
    raw_ordering = request.GET.get("ordering", "") or resource.columns[0].key
    try:
        per_page = int(request.GET.get("per_page", 25))
    except ValueError:
        per_page = 25
    if per_page not in PER_PAGE_OPTIONS:
        per_page = 25

    queryset = _base_queryset(resource)
    queryset = _apply_search(queryset, resource, query)
    queryset = _apply_filters(queryset, resource, request.GET)
    queryset = _apply_ordering(queryset, resource, raw_ordering)

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    filter_controls = [
        {
            "spec": spec,
            "value": request.GET.get(spec.param, ""),
            "options": _filter_options(resource, spec),
        }
        for spec in resource.filters
    ]
    active_filter_count = sum(1 for item in filter_controls if item["value"] != "")
    columns = []
    ordering_map = _ordering_map(resource)
    for column in resource.columns:
        current_key = raw_ordering.lstrip("-")
        current_desc = raw_ordering.startswith("-")
        next_ordering = (
            column.key if current_key != column.key or current_desc else f"-{column.key}"
        )
        columns.append(
            {
                "column": column,
                "sortable": column.key in ordering_map,
                "active": current_key == column.key,
                "descending": current_key == column.key and current_desc,
                "url": f"?{_query_string(request.GET, ordering=next_ordering, page=None)}",
            }
        )

    context = {
        "resource": resource,
        "area": AREAS[resource.area],
        "columns": columns,
        "rows": _build_rows(request, resource, page_obj.object_list),
        "page_obj": page_obj,
        "paginator": paginator,
        "query": query,
        "ordering": raw_ordering,
        "per_page": per_page,
        "per_page_options": PER_PAGE_OPTIONS,
        "filters": filter_controls,
        "active_filter_count": active_filter_count,
        "can_create": pode_acao(request.user, resource, "add") and resource.allow_create,
        "can_import_sig": resource.slug == "usuarios"
        and pode_importar_usuario_sig(getattr(request, "real_user", request.user)),
        "query_without_page": _query_string(request.GET, page=None),
    }
    partial = (
        request.GET.get("partial") == "1"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )
    template = "cadastros/_grid.html" if partial else "cadastros/lista.html"
    return render(request, template, context)


def _group_fields(form, resource: CadastroConfig):
    if not resource.form_sections:
        return [("Dados do cadastro", list(form))]
    sections = []
    used = set()
    for title, field_names in resource.form_sections:
        fields = [form[name] for name in field_names if name in form.fields]
        used.update(field_names)
        if fields:
            sections.append((title, fields))
    remaining = [field for field in form if field.name not in used]
    if remaining:
        sections.append(("Outros dados", remaining))
    return sections


def _save_form(request, resource: CadastroConfig, form, *, creating: bool):
    obj = form.save(commit=False)
    if hasattr(obj, "created_by_id") and creating:
        obj.created_by = request.user
    if hasattr(obj, "updated_by_id"):
        obj.updated_by = request.user
    obj.save()
    form.save_m2m()
    return obj


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def criar(request, resource_slug):
    resource = _resource_or_404(resource_slug)
    _require_permission(request, resource, "add")
    if not resource.allow_create or not resource.form_class:
        raise PermissionDenied
    form = resource.form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = _save_form(request, resource, form, creating=True)
        posteriores = snapshot_model(obj)
        registrar_mudanca(
            request,
            tipo=EventoAuditoria.Tipo.CADASTRO_CRIADO,
            categoria=EventoAuditoria.Categoria.CADASTRO,
            descricao=f"Registro criado em {resource.title}: {obj}.",
            objeto=obj,
            anteriores={},
            posteriores=posteriores,
            usuario_afetado=obj if isinstance(obj, Usuario) else None,
            dados={"cadastro": resource.slug},
        )
        messages.success(request, f"{resource.title}: registro criado com sucesso.")
        return redirect("cadastros:lista", resource_slug=resource.slug)
    return render(
        request,
        "cadastros/form.html",
        {
            "resource": resource,
            "area": AREAS[resource.area],
            "form": form,
            "sections": _group_fields(form, resource),
            "editing": False,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar(request, resource_slug, object_id):
    resource = _resource_or_404(resource_slug)
    _require_permission(request, resource, "change")
    if not resource.allow_update or not resource.form_class:
        raise PermissionDenied
    obj = _get_object(resource, object_id)
    anteriores = snapshot_model(obj) if request.method == "POST" else {}
    form = resource.form_class(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = _save_form(request, resource, form, creating=False)
        posteriores = snapshot_model(obj)
        registrar_mudanca(
            request,
            tipo=EventoAuditoria.Tipo.CADASTRO_ALTERADO,
            categoria=EventoAuditoria.Categoria.CADASTRO,
            descricao=f"Registro alterado em {resource.title}: {obj}.",
            objeto=obj,
            anteriores=anteriores,
            posteriores=posteriores,
            usuario_afetado=obj if isinstance(obj, Usuario) else None,
            dados={"cadastro": resource.slug},
        )
        messages.success(request, f"{resource.title}: alterações salvas com sucesso.")
        return redirect("cadastros:lista", resource_slug=resource.slug)
    return render(
        request,
        "cadastros/form.html",
        {
            "resource": resource,
            "area": AREAS[resource.area],
            "form": form,
            "sections": _group_fields(form, resource),
            "object": obj,
            "editing": True,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def excluir(request, resource_slug, object_id):
    resource = _resource_or_404(resource_slug)
    _require_permission(request, resource, "delete")
    if not resource.allow_delete:
        raise PermissionDenied
    obj = _get_object(resource, object_id)
    if request.method == "POST":
        anteriores = snapshot_model(obj)
        usuario_afetado = obj if isinstance(obj, Usuario) else None
        try:
            obj.delete()
        except ProtectedError:
            messages.error(
                request,
                "O registro possui vínculos e não pode ser excluído. "
                "Inative-o para preservar o histórico.",
            )
        else:
            registrar_mudanca(
                request,
                tipo=EventoAuditoria.Tipo.CADASTRO_EXCLUIDO,
                categoria=EventoAuditoria.Categoria.CADASTRO,
                descricao=f"Registro excluído de {resource.title}: {obj}.",
                objeto=obj,
                anteriores=anteriores,
                posteriores={},
                usuario_afetado=usuario_afetado,
                dados={"cadastro": resource.slug},
            )
            messages.success(request, "Registro excluído com sucesso.")
        return redirect("cadastros:lista", resource_slug=resource.slug)
    return render(
        request,
        "cadastros/confirmar_exclusao.html",
        {"resource": resource, "area": AREAS[resource.area], "object": obj},
    )


@login_required
@require_http_methods(["GET", "POST"])
def importar_usuario_sig(request):
    ator = getattr(request, "real_user", request.user)
    if not pode_importar_usuario_sig(ator):
        raise PermissionDenied
    form = ImportarUsuarioSIGForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            result = ImportarUsuarioSIGService().execute(
                **form.service_kwargs(),
                correlation_id=getattr(request, "request_id", ""),
            )
        except IntegrationError as exc:
            messages.error(request, str(exc))
        else:
            registrar_evento(
                request,
                tipo=EventoAuditoria.Tipo.IMPORTACAO_USUARIO_SIG,
                categoria=EventoAuditoria.Categoria.INTEGRACAO,
                ator=ator,
                usuario_afetado=result.usuario,
                objeto=result.usuario,
                descricao=f"Usuário {result.usuario.username} importado ou atualizado pelo SIG.",
                dados_posteriores=snapshot_model(result.usuario),
                dados={
                    "tipo_identificador": form.cleaned_data["tipo_identificador"],
                    "vinculos_sincronizados": result.vinculos_count,
                    "id_usuario_externo": result.identidade.id_usuario_externo,
                    "id_institucional": result.identidade.id_institucional,
                },
            )
            messages.success(
                request,
                f"{result.usuario} foi importado ou atualizado com sucesso. "
                f"{result.vinculos_count} vínculo(s) funcional(is) sincronizado(s).",
            )
            return redirect("cadastros:lista", resource_slug="usuarios")
    return render(
        request,
        "cadastros/importar_usuario_sig.html",
        {
            "form": form,
            "resource": _resource_or_404("usuarios"),
            "area": AREAS["pessoas-acessos"],
        },
    )


@login_required
def evento_auditoria_detalhe(request, uuid):
    resource = _resource_or_404("eventos-auditoria")
    _require_permission(request, resource, "view")
    evento = get_object_or_404(
        EventoAuditoria.objects.select_related("ator", "usuario_afetado"),
        uuid=uuid,
    )
    return render(
        request,
        "cadastros/evento_auditoria_detalhe.html",
        {
            "evento": evento,
            "resource": resource,
            "area": AREAS[resource.area],
            "anteriores_json": pretty_json(evento.dados_anteriores),
            "posteriores_json": pretty_json(evento.dados_posteriores),
            "dados_json": pretty_json(evento.dados),
        },
    )
