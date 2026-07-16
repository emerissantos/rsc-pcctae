from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db import models

from apps.auditoria.models import EventoAuditoria, SessaoImpersonacao
from apps.comissoes.models import Comissao, MembroComissao
from apps.contas.models import Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.triagem.models import ConfiguracaoTriagem, ItemChecklistTriagem

from .forms import (
    ComissaoForm,
    ConfiguracaoTriagemForm,
    ItemChecklistTriagemForm,
    ItemPontuacaoForm,
    MembroComissaoForm,
    NivelRSCForm,
    RequisitoForm,
    UsuarioAcessoForm,
)

Accessor = str | Callable[[Any], Any]


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    accessor: Accessor
    ordering: str | None = None
    kind: str = "text"
    css_class: str = ""


@dataclass(frozen=True)
class Filter:
    param: str
    label: str
    lookup: str
    kind: str = "auto"
    choices: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CadastroConfig:
    slug: str
    area: str
    model: type[models.Model]
    title: str
    description: str
    icon: str
    columns: tuple[Column, ...]
    search_fields: tuple[str, ...] = ()
    filters: tuple[Filter, ...] = ()
    default_ordering: str = "pk"
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    form_class: type | None = None
    allow_create: bool = True
    allow_update: bool = True
    allow_delete: bool = False
    singleton: bool = False
    form_sections: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def app_label(self) -> str:
        return self.model._meta.app_label

    @property
    def model_name(self) -> str:
        return self.model._meta.model_name

    def permission(self, action: str) -> str:
        return f"{self.app_label}.{action}_{self.model_name}"


@dataclass(frozen=True)
class CadastroArea:
    slug: str
    title: str
    description: str
    icon: str
    accent: str = "blue"
    resources: tuple[str, ...] = field(default_factory=tuple)


def _vigencia(obj) -> str:
    fim = obj.fim_vigencia.strftime("%d/%m/%Y") if obj.fim_vigencia else "sem término"
    return f"{obj.inicio_vigencia:%d/%m/%Y} a {fim}"


def _mandato(obj) -> str:
    fim = obj.fim_mandato.strftime("%d/%m/%Y") if obj.fim_mandato else "sem término"
    return f"{obj.inicio_mandato:%d/%m/%Y} a {fim}"


def _perfis_usuario(obj) -> str:
    nomes = list(obj.groups.order_by("name").values_list("name", flat=True))
    return ", ".join(nomes) if nomes else "Requerente"


RESOURCES: dict[str, CadastroConfig] = {
    "usuarios": CadastroConfig(
        slug="usuarios",
        area="pessoas-acessos",
        model=Usuario,
        title="Usuários",
        description="Contas autenticadas e situação de acesso ao sistema.",
        icon="U",
        columns=(
            Column("username", "Login", "username", "username"),
            Column("nome", "Nome", lambda obj: str(obj), "nome_exibicao"),
            Column("email", "E-mail", "email", "email"),
            Column("ativo", "Ativo", "is_active", "is_active", "bool"),
            Column("perfis", "Perfis de acesso", _perfis_usuario, "groups__name", "truncate"),
        ),
        search_fields=(
            "username",
            "nome_exibicao",
            "first_name",
            "last_name",
            "email",
            "groups__name",
        ),
        filters=(
            Filter("ativo", "Situação", "is_active", "boolean"),
            Filter("perfil", "Perfil de acesso", "groups", "foreign"),
        ),
        default_ordering="username",
        prefetch_related=("groups",),
        form_class=UsuarioAcessoForm,
        allow_create=False,
        allow_update=True,
        form_sections=(("Acesso ao sistema", ("is_active", "groups")),),
    ),
    "pessoas": CadastroConfig(
        slug="pessoas",
        area="pessoas-acessos",
        model=PessoaInstitucional,
        title="Pessoas institucionais",
        description="Pessoas recebidas da fonte institucional oficial.",
        icon="P",
        columns=(
            Column("nome", "Nome", "nome", "nome"),
            Column("id", "ID institucional", "id_institucional", "id_institucional"),
            Column("email", "E-mail", "email_institucional", "email_institucional"),
            Column("ativo", "Ativo na origem", "ativo_na_origem", "ativo_na_origem", "bool"),
            Column(
                "sincronizado", "Sincronizado em", "sincronizado_em", "sincronizado_em", "datetime"
            ),
        ),
        search_fields=("nome", "nome_identificacao", "email_institucional", "id_institucional"),
        filters=(Filter("ativo", "Ativo na origem", "ativo_na_origem", "boolean"),),
        default_ordering="nome",
        allow_create=False,
        allow_update=False,
    ),
    "servidores": CadastroConfig(
        slug="servidores",
        area="pessoas-acessos",
        model=Servidor,
        title="Servidores",
        description="Servidores sincronizados e vinculados às pessoas institucionais.",
        icon="S",
        columns=(
            Column("nome", "Nome", "nome_atual", "nome_atual"),
            Column("email", "E-mail", "email_atual", "email_atual"),
            Column("id", "ID institucional", "pessoa.id_institucional", "pessoa__id_institucional"),
            Column("ativo", "Ativo", "ativo", "ativo", "bool"),
            Column(
                "sincronizado",
                "Última sincronização",
                "ultima_sincronizacao_em",
                "ultima_sincronizacao_em",
                "datetime",
            ),
        ),
        search_fields=(
            "nome_atual",
            "nome_identificacao_atual",
            "email_atual",
            "pessoa__id_institucional",
        ),
        filters=(Filter("ativo", "Situação", "ativo", "boolean"),),
        default_ordering="nome_atual",
        select_related=("pessoa",),
        allow_create=False,
        allow_update=False,
    ),
    "vinculos": CadastroConfig(
        slug="vinculos",
        area="pessoas-acessos",
        model=VinculoFuncional,
        title="Vínculos funcionais",
        description="Vínculos, cargos, lotações e unidades de exercício sincronizados.",
        icon="V",
        columns=(
            Column("siape", "SIAPE", "siape", "siape"),
            Column("servidor", "Servidor", "servidor.nome_atual", "servidor__nome_atual"),
            Column("cargo", "Cargo", "cargo_nome", "cargo_nome"),
            Column("lotacao", "Lotação", "lotacao_nome", "lotacao_nome"),
            Column(
                "exercicio",
                "Unidade de exercício",
                "unidade_exercicio_nome",
                "unidade_exercicio_nome",
            ),
            Column("ativo", "Ativo", "ativo", "ativo", "bool"),
        ),
        search_fields=(
            "siape",
            "servidor__nome_atual",
            "cargo_nome",
            "lotacao_nome",
            "unidade_exercicio_nome",
        ),
        filters=(Filter("ativo", "Situação", "ativo", "boolean"),),
        default_ordering="servidor__nome_atual",
        select_related=("servidor",),
        allow_create=False,
        allow_update=False,
    ),
    "comissoes": CadastroConfig(
        slug="comissoes",
        area="comissoes",
        model=Comissao,
        title="Comissões",
        description="Comissões, vigências e atos de designação.",
        icon="C",
        columns=(
            Column("nome", "Comissão", "nome", "nome"),
            Column("sigla", "Sigla", "sigla", "sigla"),
            Column("ato", "Ato de designação", "ato_designacao", "ato_designacao"),
            Column("vigencia", "Vigência", _vigencia, "inicio_vigencia"),
            Column("ativa", "Situação", "ativa", "ativa", "bool"),
        ),
        search_fields=("nome", "sigla", "ato_designacao", "observacoes"),
        filters=(
            Filter("ativa", "Situação", "ativa", "boolean"),
            Filter("inicio_de", "Início da vigência a partir de", "inicio_vigencia__gte", "date"),
            Filter("inicio_ate", "Início da vigência até", "inicio_vigencia__lte", "date"),
        ),
        default_ordering="-inicio_vigencia",
        form_class=ComissaoForm,
        form_sections=(
            ("Identificação", ("nome", "sigla", "ato_designacao")),
            ("Vigência", ("inicio_vigencia", "fim_vigencia", "ativa")),
            ("Observações", ("observacoes",)),
        ),
    ),
    "membros": CadastroConfig(
        slug="membros",
        area="comissoes",
        model=MembroComissao,
        title="Membros das comissões",
        description="Titulares da atuação, função, mandato e vínculo com o usuário do sistema.",
        icon="M",
        columns=(
            Column("nome", "Membro", "nome_snapshot", "nome_snapshot"),
            Column("comissao", "Comissão", "comissao", "comissao__nome"),
            Column("papel", "Papel", "get_papel_display", "papel", "badge"),
            Column("mandato", "Mandato", _mandato, "inicio_mandato"),
            Column("ativo", "Situação", "ativo", "ativo", "bool"),
        ),
        search_fields=(
            "nome_snapshot",
            "email_snapshot",
            "usuario__username",
            "comissao__nome",
            "comissao__sigla",
        ),
        filters=(
            Filter("comissao", "Comissão", "comissao", "foreign"),
            Filter("papel", "Papel", "papel", "choices"),
            Filter("ativo", "Situação", "ativo", "boolean"),
        ),
        default_ordering="comissao__nome",
        select_related=("comissao", "usuario"),
        form_class=MembroComissaoForm,
        form_sections=(
            ("Comissão e função", ("comissao", "papel", "ativo")),
            ("Pessoa", ("usuario", "nome_snapshot", "email_snapshot")),
            ("Mandato", ("inicio_mandato", "fim_mandato")),
        ),
    ),
    "requisitos": CadastroConfig(
        slug="requisitos",
        area="pontuacao",
        model=Requisito,
        title="Requisitos",
        description="Agrupadores estruturais dos itens de pontuação.",
        icon="R",
        columns=(
            Column("codigo", "Código", "codigo", "codigo"),
            Column("nome", "Nome", "nome", "nome"),
            Column("ordem", "Ordem", "ordem", "ordem", "number"),
            Column("ativo", "Situação", "ativo", "ativo", "bool"),
        ),
        search_fields=("codigo", "nome", "descricao"),
        filters=(Filter("ativo", "Situação", "ativo", "boolean"),),
        default_ordering="ordem",
        form_class=RequisitoForm,
        form_sections=(
            ("Identificação", ("codigo", "nome", "descricao")),
            ("Organização", ("ordem", "ativo")),
        ),
    ),
    "itens-pontuacao": CadastroConfig(
        slug="itens-pontuacao",
        area="pontuacao",
        model=ItemPontuacao,
        title="Itens de pontuação",
        description="Itens, unidades, valores, limites e exigência de comprovantes.",
        icon="I",
        columns=(
            Column("codigo", "Código", "codigo", "codigo"),
            Column("requisito", "Requisito", "requisito.codigo", "requisito__ordem"),
            Column("descricao", "Descrição", "descricao", "descricao", "truncate"),
            Column("pontos", "Pontos", "pontos_por_quantidade", "pontos_por_quantidade", "decimal"),
            Column("limite", "Limite", "limite_pontos", "limite_pontos", "decimal"),
            Column("ativo", "Situação", "ativo", "ativo", "bool"),
        ),
        search_fields=("codigo", "descricao", "unidade", "orientacao", "requisito__nome"),
        filters=(
            Filter("requisito", "Requisito", "requisito", "foreign"),
            Filter("tipo", "Tipo de quantidade", "tipo_quantidade", "choices"),
            Filter("exige_anexo", "Exige comprovante", "exige_anexo", "boolean"),
            Filter("ativo", "Situação", "ativo", "boolean"),
        ),
        default_ordering="requisito__ordem",
        select_related=("requisito",),
        form_class=ItemPontuacaoForm,
        form_sections=(
            ("Identificação", ("requisito", "codigo", "descricao", "unidade")),
            (
                "Cálculo",
                ("pontos_por_quantidade", "limite_pontos", "tipo_quantidade"),
            ),
            (
                "Comprovação e orientação",
                ("exige_anexo", "observacao_permitida", "orientacao"),
            ),
            ("Organização", ("ordem", "ativo")),
        ),
    ),
    "niveis-rsc": CadastroConfig(
        slug="niveis-rsc",
        area="pontuacao",
        model=NivelRSC,
        title="Níveis de RSC",
        description="Pontuação mínima e requisitos obrigatórios de cada nível.",
        icon="N",
        columns=(
            Column("codigo", "Código", "codigo", "codigo"),
            Column("nome", "Nível", "nome", "nome"),
            Column(
                "pontuacao", "Pontuação mínima", "pontuacao_minima", "pontuacao_minima", "decimal"
            ),
            Column(
                "itens",
                "Mínimo de itens",
                "quantidade_minima_itens",
                "quantidade_minima_itens",
                "number",
            ),
            Column("ativo", "Situação", "ativo", "ativo", "bool"),
        ),
        search_fields=("codigo", "nome", "descricao"),
        filters=(Filter("ativo", "Situação", "ativo", "boolean"),),
        default_ordering="ordem",
        prefetch_related=("requisitos_obrigatorios",),
        form_class=NivelRSCForm,
        form_sections=(
            ("Identificação", ("codigo", "nome", "descricao")),
            (
                "Critérios",
                (
                    "pontuacao_minima",
                    "quantidade_minima_itens",
                    "requisitos_obrigatorios",
                ),
            ),
            ("Organização", ("ordem", "ativo")),
        ),
    ),
    "checklist-triagem": CadastroConfig(
        slug="checklist-triagem",
        area="triagem",
        model=ItemChecklistTriagem,
        title="Checklist de triagem",
        description="Itens usados nas novas rodadas de conferência documental.",
        icon="T",
        columns=(
            Column("codigo", "Código", "codigo", "codigo"),
            Column("titulo", "Item", "titulo", "titulo"),
            Column("ordem", "Ordem", "ordem", "ordem", "number"),
            Column("obrigatorio", "Obrigatório", "obrigatorio", "obrigatorio", "bool"),
            Column(
                "comprovantes",
                "Confere comprovantes",
                "confere_comprovantes",
                "confere_comprovantes",
                "bool",
            ),
            Column("ativo", "Situação", "ativo", "ativo", "bool"),
        ),
        search_fields=("codigo", "titulo", "descricao"),
        filters=(
            Filter("obrigatorio", "Obrigatório", "obrigatorio", "boolean"),
            Filter("comprovantes", "Confere comprovantes", "confere_comprovantes", "boolean"),
            Filter("ativo", "Situação", "ativo", "boolean"),
        ),
        default_ordering="ordem",
        form_class=ItemChecklistTriagemForm,
        form_sections=(
            ("Identificação", ("codigo", "titulo", "descricao")),
            (
                "Comportamento",
                ("obrigatorio", "confere_comprovantes", "ativo"),
            ),
            ("Organização", ("ordem",)),
        ),
    ),
    "eventos-auditoria": CadastroConfig(
        slug="eventos-auditoria",
        area="auditoria-suporte",
        model=EventoAuditoria,
        title="Eventos de auditoria",
        description="Importações e ações técnicas relevantes registradas pelo sistema.",
        icon="A",
        columns=(
            Column("tipo", "Evento", "get_tipo_display", "tipo", "badge"),
            Column("ator", "Realizado por", "ator", "ator__username"),
            Column("afetado", "Usuário afetado", "usuario_afetado", "usuario_afetado__username"),
            Column("descricao", "Descrição", "descricao", "descricao", "truncate"),
            Column("data", "Registrado em", "created_at", "created_at", "datetime"),
        ),
        search_fields=(
            "ator__username",
            "ator__nome_exibicao",
            "usuario_afetado__username",
            "usuario_afetado__nome_exibicao",
            "descricao",
            "request_id",
        ),
        filters=(Filter("tipo", "Tipo de evento", "tipo", "choices"),),
        default_ordering="-created_at",
        select_related=("ator", "usuario_afetado"),
        allow_create=False,
        allow_update=False,
    ),
    "sessoes-simulacao": CadastroConfig(
        slug="sessoes-simulacao",
        area="auditoria-suporte",
        model=SessaoImpersonacao,
        title="Sessões de simulação",
        description="Histórico de acessos realizados com a funcionalidade Logar como.",
        icon="◎",
        columns=(
            Column("ator", "Usuário técnico", "ator", "ator__username"),
            Column("alvo", "Usuário simulado", "usuario_simulado", "usuario_simulado__username"),
            Column("justificativa", "Justificativa", "justificativa", "justificativa", "truncate"),
            Column("inicio", "Iniciada em", "iniciada_em", "iniciada_em", "datetime"),
            Column("fim", "Encerrada em", "encerrada_em", "encerrada_em", "datetime"),
        ),
        search_fields=(
            "ator__username",
            "ator__nome_exibicao",
            "usuario_simulado__username",
            "usuario_simulado__nome_exibicao",
            "justificativa",
            "request_id_inicio",
        ),
        filters=(Filter("ativa", "Sessão ativa", "encerrada_em__isnull", "boolean"),),
        default_ordering="-iniciada_em",
        select_related=("ator", "usuario_simulado", "encerrada_por"),
        allow_create=False,
        allow_update=False,
    ),
    "configuracao-triagem": CadastroConfig(
        slug="configuracao-triagem",
        area="triagem",
        model=ConfiguracaoTriagem,
        title="Configuração da triagem",
        description="Prazo institucional aplicado às novas pendências de correção.",
        icon="⚙",
        columns=(
            Column(
                "prazo", "Prazo para correção", "get_prazo_correcao_dias_display", None, "badge"
            ),
            Column("atualizado", "Atualizado em", "updated_at", "updated_at", "datetime"),
        ),
        default_ordering="pk",
        form_class=ConfiguracaoTriagemForm,
        allow_create=False,
        singleton=True,
        form_sections=(("Prazo de correção", ("prazo_correcao_dias",)),),
    ),
}


AREAS: dict[str, CadastroArea] = {
    "pessoas-acessos": CadastroArea(
        slug="pessoas-acessos",
        title="Pessoas e acessos",
        description="Consulta de usuários, pessoas, servidores e vínculos sincronizados.",
        icon="P",
        accent="blue",
        resources=("usuarios", "pessoas", "servidores", "vinculos"),
    ),
    "comissoes": CadastroArea(
        slug="comissoes",
        title="Comissões",
        description="Gestão de comissões, membros, papéis e vigências.",
        icon="C",
        accent="orange",
        resources=("comissoes", "membros"),
    ),
    "pontuacao": CadastroArea(
        slug="pontuacao",
        title="Pontuação",
        description="Níveis, requisitos e itens usados no cálculo dos requerimentos.",
        icon="∑",
        accent="purple",
        resources=("niveis-rsc", "requisitos", "itens-pontuacao"),
    ),
    "triagem": CadastroArea(
        slug="triagem",
        title="Triagem",
        description="Checklist documental e parâmetros aplicados às novas rodadas.",
        icon="✓",
        accent="green",
        resources=("checklist-triagem", "configuracao-triagem"),
    ),
    "auditoria-suporte": CadastroArea(
        slug="auditoria-suporte",
        title="Auditoria e suporte",
        description="Importações institucionais e sessões técnicas de simulação.",
        icon="A",
        accent="orange",
        resources=("eventos-auditoria", "sessoes-simulacao"),
    ),
}


def get_resource(slug: str) -> CadastroConfig:
    try:
        return RESOURCES[slug]
    except KeyError as exc:
        raise LookupError(f"Cadastro não encontrado: {slug}") from exc


def get_area(slug: str) -> CadastroArea:
    try:
        return AREAS[slug]
    except KeyError as exc:
        raise LookupError(f"Área de cadastro não encontrada: {slug}") from exc


def resolve_value(obj: Any, accessor: Accessor) -> Any:
    if callable(accessor):
        return accessor(obj)
    value = obj
    for part in accessor.split("."):
        value = getattr(value, part, None)
        if callable(value):
            value = value()
        if value is None:
            break
    return value


def format_value(value: Any, kind: str) -> dict[str, str | bool]:
    if kind == "bool":
        enabled = bool(value)
        return {
            "text": "Sim" if enabled else "Não",
            "badge": True,
            "badge_class": "success" if enabled else "neutral",
        }
    if value in (None, ""):
        return {"text": "—", "badge": False, "badge_class": ""}
    if kind == "date" and isinstance(value, date):
        return {"text": value.strftime("%d/%m/%Y"), "badge": False, "badge_class": ""}
    if kind == "datetime" and isinstance(value, datetime):
        return {
            "text": value.strftime("%d/%m/%Y %H:%M"),
            "badge": False,
            "badge_class": "",
        }
    if kind == "decimal" and isinstance(value, (Decimal, int, float)):
        text = f"{Decimal(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return {"text": text, "badge": False, "badge_class": ""}
    if kind == "badge":
        return {"text": str(value), "badge": True, "badge_class": "info"}
    return {"text": str(value), "badge": False, "badge_class": ""}
