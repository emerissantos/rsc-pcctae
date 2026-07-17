from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import EventoAuditoria
from apps.contas.models import IdentidadeExterna, Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional


@pytest.fixture
def usuario_com_dados(db):
    usuario = Usuario.objects.create_user(
        username="maria.silva",
        email="maria.silva@ufsb.edu.br",
        nome_exibicao="Maria da Silva",
    )
    pessoa = PessoaInstitucional.objects.create(
        id_institucional=9001,
        nome="Maria da Silva",
        nome_identificacao="Maria Silva",
        email_institucional="maria.silva@ufsb.edu.br",
        sincronizado_em=timezone.now(),
    )
    identidade = IdentidadeExterna.objects.create(
        pessoa=pessoa,
        usuario=usuario,
        id_usuario_externo=7001,
        id_institucional=pessoa.id_institucional,
        login=usuario.username,
        ativo_na_origem=True,
        email_recebido=usuario.email,
        nome_recebido=usuario.nome_exibicao,
        ultimo_login_em=timezone.now(),
        ultima_sincronizacao_em=timezone.now(),
    )
    servidor = Servidor.objects.create(
        pessoa=pessoa,
        nome_atual=pessoa.nome,
        nome_identificacao_atual=pessoa.nome_identificacao,
        email_atual=pessoa.email_institucional,
        ativo=True,
        ultima_sincronizacao_em=timezone.now(),
    )
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=8001,
        siape="1234567",
        digito_siape="8",
        cargo_nome="Técnico de Tecnologia da Informação",
        lotacao_nome="Superintendência de Tecnologia da Informação",
        unidade_exercicio_nome="Coordenação de Sistemas",
        regime_trabalho=40,
        data_admissao=date(2020, 2, 10),
        ativo=True,
        ultima_sincronizacao_em=timezone.now(),
    )
    return usuario, pessoa, identidade, servidor, vinculo


@pytest.mark.django_db
def test_usuario_visualiza_os_proprios_dados_funcionais(client, usuario_com_dados):
    usuario, pessoa, _, _, vinculo = usuario_com_dados
    client.force_login(usuario)

    response = client.get(reverse("core:meus-dados"))

    assert response.status_code == 200
    content = response.content.decode()
    assert pessoa.nome in content
    assert usuario.email in content
    assert vinculo.siape in content
    assert vinculo.cargo_nome in content
    assert vinculo.lotacao_nome in content
    assert "setor responsável pelo cadastro funcional" in content
    assert "Progepe" in content


@pytest.mark.django_db
def test_pagina_nao_expoe_dados_de_outro_usuario(client, usuario_com_dados):
    usuario, *_ = usuario_com_dados
    outro = Usuario.objects.create_user(username="outro.usuario", nome_exibicao="Outro Usuário")
    outra_pessoa = PessoaInstitucional.objects.create(
        id_institucional=9911,
        nome="Pessoa que não deve aparecer",
        email_institucional="privado@ufsb.edu.br",
    )
    IdentidadeExterna.objects.create(
        pessoa=outra_pessoa,
        usuario=outro,
        id_usuario_externo=7911,
        id_institucional=outra_pessoa.id_institucional,
        login=outro.username,
    )
    client.force_login(usuario)

    response = client.get(reverse("core:meus-dados"))

    content = response.content.decode()
    assert response.status_code == 200
    assert outra_pessoa.nome not in content
    assert outra_pessoa.email_institucional not in content


@pytest.mark.django_db
def test_consulta_dos_dados_funcionais_e_auditada(client, usuario_com_dados):
    usuario, *_ = usuario_com_dados
    client.force_login(usuario)

    response = client.get(
        reverse("core:meus-dados"),
        REMOTE_ADDR="200.128.32.10",
        HTTP_USER_AGENT="Teste navegador",
    )

    assert response.status_code == 200
    evento = EventoAuditoria.objects.get(
        tipo=EventoAuditoria.Tipo.DADOS_FUNCIONAIS_VISUALIZADOS
    )
    assert evento.ator == usuario
    assert evento.usuario_afetado == usuario
    assert evento.endereco_ip == "200.128.32.10"
    assert evento.dados["quantidade_vinculos"] == 1
    assert evento.dados["quantidade_vinculos_ativos"] == 1


@pytest.mark.django_db
def test_usuario_sem_sincronizacao_recebe_orientacao(client):
    usuario = Usuario.objects.create_user(
        username="sem.dados",
        email="sem.dados@ufsb.edu.br",
        nome_exibicao="Usuário sem dados",
    )
    client.force_login(usuario)

    response = client.get(reverse("core:meus-dados"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Dados funcionais ainda não sincronizados" in content
    assert "Progepe" in content


@pytest.mark.django_db
def test_nome_e_email_da_pagina_inicial_apontam_para_meus_dados(client, usuario_com_dados):
    usuario, *_ = usuario_com_dados
    client.force_login(usuario)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    content = response.content.decode()
    profile_url = reverse("core:meus-dados")
    assert content.count(f'href="{profile_url}"') >= 2
    assert usuario.nome_exibicao in content
    assert usuario.email in content


def test_meus_dados_exige_autenticacao(client):
    response = client.get(reverse("core:meus-dados"))

    assert response.status_code == 302
    assert response.url == reverse("contas:login")
