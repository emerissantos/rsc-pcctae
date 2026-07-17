from __future__ import annotations

from django.contrib.auth.models import Group, Permission

from .registry import RESOURCES, CadastroArea, CadastroConfig

CADASTRO_ACCESS_GROUP_NAMES = frozenset(
    {
        "Administradores do RSC-PCCTAE",
        "Gestão de Pessoas e Acessos",
        "Gestão de Comissões",
        "Gestão de Pontuação",
        "Gestão de Triagem",
        "Consulta de Cadastros",
    }
)


GROUP_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "Administradores do RSC-PCCTAE": tuple(
        resource.permission(action)
        for resource in RESOURCES.values()
        for action in ("view", "add", "change", "delete")
        if action == "view"
        or (action == "add" and resource.allow_create)
        or (action == "change" and resource.allow_update)
        or (action == "delete" and resource.allow_delete)
    )
    + (
        "contas.importar_usuario_sig",
        "contas.simular_usuario",
        "triagem.acessar_fila_triagem",
        "triagem.iniciar_triagem",
        "triagem.alterar_triagem",
        "triagem.concluir_triagem",
    ),
    "Gestão de Pessoas e Acessos": (
        "contas.view_usuario",
        "contas.change_usuario",
        "contas.importar_usuario_sig",
        "pessoas.view_pessoainstitucional",
        "pessoas.view_servidor",
        "pessoas.view_vinculofuncional",
    ),
    "Gestão de Comissões": (
        "comissoes.view_comissao",
        "comissoes.add_comissao",
        "comissoes.change_comissao",
        "comissoes.view_membrocomissao",
        "comissoes.add_membrocomissao",
        "comissoes.change_membrocomissao",
        "contas.view_usuario",
        "pessoas.view_pessoainstitucional",
        "pessoas.view_servidor",
        "pessoas.view_vinculofuncional",
    ),
    "Gestão de Pontuação": (
        "pontuacao.view_nivelrsc",
        "pontuacao.add_nivelrsc",
        "pontuacao.change_nivelrsc",
        "pontuacao.view_requisito",
        "pontuacao.add_requisito",
        "pontuacao.change_requisito",
        "pontuacao.view_itempontuacao",
        "pontuacao.add_itempontuacao",
        "pontuacao.change_itempontuacao",
    ),
    "Gestão de Triagem": (
        "triagem.view_itemchecklisttriagem",
        "triagem.add_itemchecklisttriagem",
        "triagem.change_itemchecklisttriagem",
        "triagem.view_configuracaotriagem",
        "triagem.change_configuracaotriagem",
        "comissoes.view_comissao",
        "comissoes.view_membrocomissao",
    ),
    "Operação de Triagem": (
        "triagem.acessar_fila_triagem",
        "triagem.iniciar_triagem",
        "triagem.alterar_triagem",
        "triagem.concluir_triagem",
        "triagem.view_triagemrequerimento",
        "triagem.view_verificacaochecklisttriagem",
        "requerimentos.view_requerimento",
        "requerimentos.view_lancamentoitem",
        "requerimentos.view_documentolancamento",
        "comissoes.view_comissao",
        "comissoes.view_membrocomissao",
    ),
    "Consulta de Cadastros": tuple(
        resource.permission("view")
        for resource in RESOURCES.values()
        if resource.app_label != "auditoria"
    ),
}


def possui_perfil_de_cadastros(user) -> bool:
    """Indica se o usuário recebeu um perfil funcional da Central de Cadastros.

    Permissões técnicas isoladas e ``is_staff`` não liberam a central. Isso evita que
    permissões necessárias em módulos operacionais — como a triagem — façam surgir
    cards administrativos para o requerente.
    """

    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=CADASTRO_ACCESS_GROUP_NAMES).exists()


def pode_acao(user, resource: CadastroConfig, action: str) -> bool:
    if not possui_perfil_de_cadastros(user):
        return False
    if user.is_superuser:
        return True
    if action == "add" and not resource.allow_create:
        return False
    if action == "change" and not resource.allow_update:
        return False
    if action == "delete" and not resource.allow_delete:
        return False
    return user.has_perm(resource.permission(action))


def recursos_visiveis(user, area: CadastroArea | None = None) -> list[CadastroConfig]:
    slugs = area.resources if area else tuple(RESOURCES)
    return [RESOURCES[slug] for slug in slugs if pode_acao(user, RESOURCES[slug], "view")]


def pode_acessar_cadastros(user) -> bool:
    return bool(recursos_visiveis(user))


def seed_groups() -> dict[str, int]:
    result: dict[str, int] = {}
    for group_name, permission_names in GROUP_DEFINITIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for permission_name in permission_names:
            app_label, codename = permission_name.split(".", 1)
            permission = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename,
            ).first()
            if permission:
                permissions.append(permission)
        group.permissions.set(permissions)
        result[group_name] = len(permissions)
    return result
