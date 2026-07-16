from __future__ import annotations

from django.contrib.auth.models import Group, Permission

from .registry import RESOURCES, CadastroArea, CadastroConfig

GROUP_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "Administradores do RSC-PCCTAE": tuple(
        resource.permission(action)
        for resource in RESOURCES.values()
        for action in ("view", "add", "change", "delete")
    ),
    "Gestão de Comissões": (
        "comissoes.view_comissao",
        "comissoes.add_comissao",
        "comissoes.change_comissao",
        "comissoes.view_membrocomissao",
        "comissoes.add_membrocomissao",
        "comissoes.change_membrocomissao",
        "contas.view_usuario",
        "pessoas.view_personainstitucional",
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
    "Consulta de Cadastros": tuple(resource.permission("view") for resource in RESOURCES.values()),
}


def pode_acao(user, resource: CadastroConfig, action: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser or user.is_staff:
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
