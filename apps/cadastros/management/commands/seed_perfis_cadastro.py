from django.core.management.base import BaseCommand

from apps.cadastros.permissions import seed_groups


class Command(BaseCommand):
    help = "Cria ou atualiza os grupos e permissões da Central de Cadastros."

    def handle(self, *args, **options):
        result = seed_groups()
        details = ", ".join(f"{name}: {count}" for name, count in result.items())
        self.stdout.write(self.style.SUCCESS(f"Perfis de cadastro atualizados — {details}."))
