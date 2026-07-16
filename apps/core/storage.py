from __future__ import annotations

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateFileSystemStorage(FileSystemStorage):
    """Storage local sem URL pública.

    Os nomes dos arquivos são persistidos no banco somente como caminhos
    internos. Qualquer leitura deve passar por uma view autenticada que aplique
    as regras de autorização do requerimento.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", settings.MEDIA_ROOT)
        super().__init__(*args, **kwargs)

    def url(self, name: str) -> str:  # pragma: no cover - proteção defensiva
        raise ValueError(
            "Arquivos privados não possuem URL pública. "
            "Use o endpoint autenticado do sistema."
        )
