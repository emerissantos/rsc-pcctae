from datetime import date

from django.test import TestCase

from apps.integracoes.ufsb.api.schemas import (
    ServidorInstitucionalDTO,
    UsuarioInstitucionalDTO,
)
from apps.pessoas.models import PessoaInstitucional, VinculoFuncional
from apps.pessoas.services import PersistirCadastroInstitucionalService


class SincronizacaoTests(TestCase):
    def test_preserva_multiplos_vinculos_da_mesma_pessoa(self):
        usuario = UsuarioInstitucionalDTO(
            id_institucional=100,
            id_usuario=200,
            id_unidade=10,
            login="fulano",
            nome_pessoa="FULANO",
            cpf_cnpj=None,
            ativo=True,
            email="fulano@ufsb.edu.br",
        )
        base = dict(
            id_institucional=100,
            nome="FULANO",
            nome_identificacao=None,
            email="fulano@ufsb.edu.br",
            digito_siape="0",
            id_ativo=1,
            id_situacao=1,
            id_categoria=1,
            id_lotacao=10,
            lotacao="UNIDADE",
            id_unidade_exercicio=10,
            unidade_exercicio="UNIDADE",
            id_cargo=1,
            cargo="CARGO",
            id_tipo_formacao=1,
            regime_trabalho=40,
            data_admissao=date(2015, 6, 1),
        )
        servidores = [
            ServidorInstitucionalDTO(id_servidor=1, siape="000001", ativo=True, **base),
            ServidorInstitucionalDTO(id_servidor=2, siape="000002", ativo=False, **base),
        ]
        result = PersistirCadastroInstitucionalService.execute(
            usuario_api=usuario,
            servidores_api=servidores,
        )
        self.assertEqual(PessoaInstitucional.objects.count(), 1)
        self.assertEqual(VinculoFuncional.objects.count(), 2)
        self.assertEqual(len(result.vinculos), 2)
