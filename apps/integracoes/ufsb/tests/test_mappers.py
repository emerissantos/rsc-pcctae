from datetime import date
from unittest import TestCase

from apps.integracoes.ufsb.api.mappers import map_servidor, map_usuario


class MapperUsuarioTests(TestCase):
    def test_mapeia_usuario_com_chaves_hifenizadas(self):
        dto = map_usuario(
            {
                "id-institucional": 201500028706,
                "id-usuario": 1,
                "id-unidade": 605,
                "login": "logins",
                "nome-pessoa": "LOGINS DE TAL",
                "cpf-cnpj": 12345678901,
                "ativo": True,
                "email": "TESTE@ufsb.edu.br",
                "id-foto": None,
                "chave-foto": None,
                "url-foto": None,
            }
        )
        self.assertEqual(dto.id_usuario, 1)
        self.assertEqual(dto.id_institucional, 201500028706)
        self.assertEqual(dto.cpf_cnpj, "12345678901")
        self.assertEqual(dto.email, "TESTE@ufsb.edu.br")


class MapperServidorTests(TestCase):
    def test_mapeia_multiplos_campos_funcionais(self):
        dto = map_servidor(
            {
                "id-servidor": 282,
                "nome": "FULANO DE TAL",
                "cpf": "11111111111",
                "sexo": "M",
                "nome-identificacao": None,
                "email": "EMAIL@ufsb.edu.br",
                "siape": "0221330",
                "digito-siape": "0",
                "id-institucional": 201500028508,
                "id-ativo": 1,
                "id-situacao": 1,
                "id-categoria": 1,
                "id-lotacao": 454,
                "lotacao": "CENTRO DE FORMAÇÃO X",
                "id-unidade-exercicio": 454,
                "unidade-exercicio": "CENTRO DE FORMAÇÃO X",
                "id-cargo": 705001,
                "cargo": "TÉCNICO ADMINISTRATIVO",
                "id-tipo-formacao": 27,
                "regime-trabalho": 40,
                "data-admissao": 1433127600000,
                "ativo": True,
            }
        )
        self.assertEqual(dto.id_servidor, 282)
        self.assertEqual(dto.siape, "0221330")
        self.assertEqual(dto.data_admissao, date(2015, 6, 1))
        self.assertTrue(dto.ativo)
