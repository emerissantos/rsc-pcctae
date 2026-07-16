from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.requerimentos.models import UploadTemporario


class Command(BaseCommand):
    help = "Remove arquivos temporários expirados que não foram vinculados a itens."

    def handle(self, *args, **options):
        total = 0
        queryset = UploadTemporario.objects.filter(
            status=UploadTemporario.Status.CONCLUIDO,
            expira_em__lt=timezone.now(),
        )
        for upload in queryset.iterator():
            upload.remover_arquivo()
            upload.delete()
            total += 1
        self.stdout.write(self.style.SUCCESS(f"{total} upload(s) temporário(s) removido(s)."))
