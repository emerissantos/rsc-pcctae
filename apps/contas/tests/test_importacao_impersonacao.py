from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.auditoria.models import EventoAuditoria, SessaoImpersonacao
from apps.contas.models import IdentidadeExterna, Usuario
from apps.contas.services import ImportarUsuarioSIGService, ProvisionResult
from apps.integracoes.ufsb.api.schemas import UsuarioInstitucionalDTO
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import NivelRSC
from apps.requerimentos.models import Requerimento


def _grant(user, codename: str):
    permission = Permission.objects.get(
        content_type__app_label="contas",
        codename=codename,
    )
    user.user_permissions.add(permission)


def _create_requirement(user: Usuario, *, institutional_id: int, siape: str):
    pessoa = PessoaInstitucional.objects.create(
        id_institucional=institutional_id,
        nome=str(user),
    )
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual=str(user))
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=institutional_id + 1000,
        siape=siape,
    )
    nivel, _ = NivelRSC.objects.get_or_create(
        codigo="I",
        defaults={
            "nome": "RSC I",
            "pontuacao_minima": Decimal("0"),
            "quantidade_minima_itens": 0,
        },
    )
    return Requerimento.objects.create(
        requerente=user,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )


@pytest.mark.django_db
def test_importacao_administrativa_cria_conta_sem_login_oauth():
    usuario_api = UsuarioInstitucionalDTO(
        id_institucional=100,
        id_usuario=200,
        id_unidade=300,
        login="servidor.teste",
        nome_pessoa="Servidor Teste",
        cpf_cnpj=None,
        ativo=True,
        email="servidor.teste@ufsb.edu.br",
    )
    usuarios_service = Mock()
    usuarios_service.get_by_identifier.return_value = usuario_api
    servidores_service = Mock()
    servidores_service.list_by_id_institucional.return_value = []

    resultado = ImportarUsuarioSIGService(
        usuarios_service=usuarios_service,
        servidores_service=servidores_service,
    ).execute(login="servidor.teste", correlation_id="req-1")

    assert resultado.usuario.username == "servidor.teste"
    assert resultado.usuario.has_usable_password() is False
    assert resultado.identidade.id_usuario_externo == 200
    assert PessoaInstitucional.objects.filter(id_institucional=100).exists()


@pytest.mark.django_db
def test_tela_importa_usuario_e_registra_auditoria(client):
    ator = Usuario.objects.create_user(username="gestor-pessoas", password="teste")
    _grant(ator, "importar_usuario_sig")
    alvo = Usuario.objects.create_user(username="importado", password="teste")
    pessoa = PessoaInstitucional.objects.create(id_institucional=901, nome="Importado")
    identidade = IdentidadeExterna.objects.create(
        usuario=alvo,
        pessoa=pessoa,
        id_usuario_externo=902,
        id_institucional=901,
        login="importado",
    )
    resultado = ProvisionResult(usuario=alvo, identidade=identidade, vinculos_count=2)
    client.force_login(ator)

    with patch("apps.cadastros.views.ImportarUsuarioSIGService") as service_class:
        service_class.return_value.execute.return_value = resultado
        resposta = client.post(
            reverse("cadastros:importar-usuario-sig"),
            {"tipo_identificador": "login", "valor": "IMPORTADO"},
        )

    assert resposta.status_code == 302
    service_class.return_value.execute.assert_called_once_with(
        login="importado",
        correlation_id=resposta.wsgi_request.request_id,
    )
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.IMPORTACAO_USUARIO_SIG)
    assert evento.ator == ator
    assert evento.usuario_afetado == alvo
    assert evento.dados["vinculos_sincronizados"] == 2


@pytest.mark.django_db
def test_importacao_exige_permissao(client):
    usuario = Usuario.objects.create_user(username="sem-permissao", password="teste")
    client.force_login(usuario)

    resposta = client.get(reverse("cadastros:importar-usuario-sig"))

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_staff_simula_usuario_em_modo_somente_leitura(client):
    ator = Usuario.objects.create_user(
        username="tecnico",
        password="teste",
        is_staff=True,
    )
    _grant(ator, "simular_usuario")
    alvo = Usuario.objects.create_user(
        username="requerente-alvo",
        password="teste",
        nome_exibicao="Requerente Alvo",
    )
    outro = Usuario.objects.create_user(username="outro", password="teste")
    requerimento_alvo = _create_requirement(alvo, institutional_id=1001, siape="1111111")
    requerimento_outro = _create_requirement(outro, institutional_id=1002, siape="2222222")
    client.force_login(ator)

    resposta = client.post(
        reverse("contas:impersonar-iniciar", args=[alvo.uuid]),
        {"justificativa": "Chamado GLPI 12345 para reproduzir falha de visualização."},
    )
    assert resposta.status_code == 302

    lista = client.get(reverse("requerimentos:lista"))
    conteudo = lista.content.decode()
    assert lista.status_code == 200
    assert "Simulando Requerente Alvo" in conteudo
    assert requerimento_alvo.numero in conteudo
    assert requerimento_outro.numero not in conteudo

    bloqueada = client.post(reverse("requerimentos:criar"), {})
    assert bloqueada.status_code == 403
    assert EventoAuditoria.objects.filter(
        tipo=EventoAuditoria.Tipo.ACAO_BLOQUEADA_IMPERSONACAO,
        ator=ator,
        usuario_afetado=alvo,
    ).exists()

    encerramento = client.post(reverse("contas:impersonar-encerrar"))
    assert encerramento.status_code == 302
    sessao = SessaoImpersonacao.objects.get(ator=ator, usuario_simulado=alvo)
    assert sessao.encerrada_em is not None
    assert sessao.encerrada_por == ator

    pagina = client.get(reverse("core:home"))
    assert "Simulando Requerente Alvo" not in pagina.content.decode()


@pytest.mark.django_db
def test_nao_permite_simular_superusuario(client):
    ator = Usuario.objects.create_user(
        username="tecnico",
        password="teste",
        is_staff=True,
    )
    _grant(ator, "simular_usuario")
    alvo = Usuario.objects.create_superuser(
        username="root-alvo",
        password="teste",
        email="root@ufsb.edu.br",
    )
    client.force_login(ator)

    resposta = client.get(reverse("contas:impersonar-iniciar", args=[alvo.uuid]))

    assert resposta.status_code == 403
