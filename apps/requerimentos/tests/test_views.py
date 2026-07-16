from decimal import Decimal

import pytest
from django.urls import reverse

from apps.contas.models import IdentidadeExterna, Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import NivelRSC
from apps.requerimentos.models import Requerimento


@pytest.mark.django_db
def test_usuario_cria_requerimento(client):
    usuario = Usuario.objects.create_user(username="servidor", password="teste")
    pessoa = PessoaInstitucional.objects.create(id_institucional=10, nome="Servidor Teste")
    IdentidadeExterna.objects.create(
        usuario=usuario,
        pessoa=pessoa,
        id_usuario_externo=1,
        id_institucional=10,
        login="servidor",
    )
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual="Servidor Teste")
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=20,
        siape="1234567",
        cargo_nome="Técnico",
    )
    nivel = NivelRSC.objects.create(
        codigo="I",
        nome="RSC I",
        pontuacao_minima=Decimal("10.00"),
        quantidade_minima_itens=1,
    )
    client.force_login(usuario)
    response = client.post(
        reverse("requerimentos:criar"),
        {"vinculo": vinculo.pk, "nivel_pretendido": nivel.pk, "observacao_geral": ""},
    )
    assert response.status_code == 302
    requerimento = Requerimento.objects.get(requerente=usuario)
    assert client.get(reverse("requerimentos:itens", args=[requerimento.uuid])).status_code == 200
