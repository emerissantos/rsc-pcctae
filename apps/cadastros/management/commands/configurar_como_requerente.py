from django.core.management.base import BaseCommand, CommandError

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import diff_snapshots, snapshot_model
from apps.cadastros.permissions import GROUP_DEFINITIONS
from apps.contas.models import Usuario


class Command(BaseCommand):
    help = (
        "Remove perfis funcionais, permissões diretas e flags administrativas de uma conta, "
        "mantendo-a somente como requerente."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", help="Login institucional do usuário.")
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Confirma a remoção dos acessos funcionais e administrativos.",
        )

    def handle(self, *args, **options):
        if not options["confirmar"]:
            raise CommandError(
                "Operação não executada. Repita o comando com --confirmar após revisar o login."
            )

        username = options["username"].strip()
        try:
            usuario = Usuario.objects.get(username__iexact=username)
        except Usuario.DoesNotExist as exc:
            raise CommandError(f"Usuário não encontrado: {username}") from exc

        anteriores = snapshot_model(usuario)
        grupos = list(
            usuario.groups.filter(name__in=tuple(GROUP_DEFINITIONS)).values_list(
                "name", flat=True
            )
        )
        permissoes_diretas = usuario.user_permissions.count()

        usuario.groups.remove(*usuario.groups.filter(name__in=tuple(GROUP_DEFINITIONS)))
        usuario.user_permissions.clear()
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.save(update_fields=["is_staff", "is_superuser"])
        posteriores = snapshot_model(usuario)
        EventoAuditoria.objects.create(
            tipo=EventoAuditoria.Tipo.CADASTRO_ALTERADO,
            categoria=EventoAuditoria.Categoria.CADASTRO,
            nivel=EventoAuditoria.Nivel.ATENCAO,
            usuario_afetado=usuario,
            descricao=(
                f"Usuário {usuario.username} configurado como requerente por comando "
                "de gerenciamento."
            ),
            recurso="Usuários e perfis de acesso",
            objeto_tipo="contas.usuario",
            objeto_id=str(usuario.uuid),
            objeto_representacao=str(usuario),
            metodo_http="COMMAND",
            caminho="manage.py configurar_como_requerente",
            dados_anteriores=anteriores,
            dados_posteriores=posteriores,
            campos_alterados=diff_snapshots(anteriores, posteriores),
            dados={
                "perfis_removidos": grupos,
                "permissoes_diretas_removidas": permissoes_diretas,
            },
        )

        grupos_texto = ", ".join(grupos) if grupos else "nenhum"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuário {usuario.username} configurado como requerente. "
                f"Perfis removidos: {grupos_texto}. "
                f"Permissões diretas removidas: {permissoes_diretas}."
            )
        )
