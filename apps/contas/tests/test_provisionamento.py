from unittest.mock import Mock

from django.test import TestCase

from apps.contas.models import IdentidadeExterna, Usuario
from apps.contas.services import ProvisionarUsuarioUFSBService
from apps.integracoes.ufsb.api.schemas import UsuarioInstitucionalDTO
from apps.integracoes.ufsb.oauth.schemas import OAuthUserInfo
from apps.pessoas.models import PessoaInstitucional
from apps.pessoas.services import SyncResult


class ProvisionamentoTests(TestCase):
    def test_provisionamento_e_idempotente_por_id_usuario(self):
        userinfo = OAuthUserInfo(
            id_usuario=10,
            id_institucional=20,
            login="fulano",
            nome="FULANO",
            email="fulano@ufsb.edu.br",
            raw={},
        )
        dto = UsuarioInstitucionalDTO(
            id_institucional=20,
            id_usuario=10,
            id_unidade=1,
            login="fulano",
            nome_pessoa="FULANO",
            cpf_cnpj=None,
            ativo=True,
            email="fulano@ufsb.edu.br",
        )
        pessoa = PessoaInstitucional.objects.create(id_institucional=20, nome="FULANO")
        usuarios_service = Mock()
        usuarios_service.resolve_from_userinfo.return_value = dto
        servidores_service = Mock()
        servidores_service.list_by_id_institucional.return_value = []

        with self.subTest("primeiro acesso"), self.settings():
            from unittest.mock import patch

            with patch(
                "apps.contas.services.PersistirCadastroInstitucionalService.execute",
                return_value=SyncResult(
                    pessoa=pessoa,
                    servidor=None,
                    vinculos=(),
                    created_count=0,
                    updated_count=1,
                ),
            ):
                service = ProvisionarUsuarioUFSBService(
                    usuarios_service=usuarios_service,
                    servidores_service=servidores_service,
                )
                first = service.execute(userinfo=userinfo)
                second = service.execute(userinfo=userinfo)

        self.assertEqual(first.usuario.pk, second.usuario.pk)
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(IdentidadeExterna.objects.count(), 1)
        self.assertFalse(first.usuario.has_usable_password())
