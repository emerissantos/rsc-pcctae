from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.contas.models import IdentidadeExterna, Usuario


class IdentidadeExternaTests(TestCase):
    def test_identidade_e_unica_por_provedor_e_id_usuario(self):
        primeiro = Usuario.objects.create_user(username="primeiro")
        segundo = Usuario.objects.create_user(username="segundo")
        IdentidadeExterna.objects.create(
            usuario=primeiro,
            provedor="sigauth_ufsb",
            id_usuario_externo=10,
            login="primeiro.login",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            IdentidadeExterna.objects.create(
                usuario=segundo,
                provedor="sigauth_ufsb",
                id_usuario_externo=10,
                login="segundo.login",
            )
