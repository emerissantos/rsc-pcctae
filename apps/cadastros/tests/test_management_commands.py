import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

from apps.auditoria.models import EventoAuditoria
from apps.cadastros.permissions import seed_groups
from apps.contas.models import Usuario


@pytest.mark.django_db
def test_configurar_como_requerente_remove_acessos_funcionais():
    seed_groups()
    usuario = Usuario.objects.create_user(
        username="antigo-gestor",
        password="teste",
        is_staff=True,
        is_superuser=True,
    )
    usuario.groups.add(
        Group.objects.get(name="Administradores do RSC-PCCTAE"),
        Group.objects.get(name="Operação de Triagem"),
    )
    usuario.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="pontuacao",
            codename="view_nivelrsc",
        )
    )

    call_command("configurar_como_requerente", usuario.username, confirmar=True)

    usuario.refresh_from_db()
    assert usuario.is_staff is False
    assert usuario.is_superuser is False
    assert usuario.groups.count() == 0
    assert usuario.user_permissions.count() == 0

    evento = EventoAuditoria.objects.get(
        tipo=EventoAuditoria.Tipo.CADASTRO_ALTERADO,
        usuario_afetado=usuario,
    )
    assert evento.metodo_http == "COMMAND"
    assert "groups" in evento.campos_alterados
    assert evento.dados["permissoes_diretas_removidas"] == 1
