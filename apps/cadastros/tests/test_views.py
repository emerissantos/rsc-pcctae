from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from django.utils import timezone

from apps.cadastros.permissions import seed_groups
from apps.comissoes.models import Comissao
from apps.contas.models import Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import NivelRSC
from apps.requerimentos.models import Requerimento


@pytest.fixture
def staff_user(db):
    seed_groups()
    usuario = Usuario.objects.create_user(
        username="gestor",
        password="teste",
        is_staff=True,
    )
    usuario.groups.add(Group.objects.get(name="Administradores do RSC-PCCTAE"))
    return usuario


@pytest.mark.django_db
def test_usuario_sem_permissao_nao_acessa_central(client):
    usuario = Usuario.objects.create_user(username="requerente", password="teste")
    client.force_login(usuario)

    resposta = client.get(reverse("cadastros:central"))

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_administrador_com_perfil_visualiza_areas_em_cards(client, staff_user):
    client.force_login(staff_user)

    resposta = client.get(reverse("cadastros:central"))

    assert resposta.status_code == 200
    assert "Pessoas e acessos" in resposta.content.decode()
    assert "Comissões" in resposta.content.decode()
    assert "Pontuação" in resposta.content.decode()
    assert "Triagem" in resposta.content.decode()


@pytest.mark.django_db
def test_grupo_restringe_cards_as_areas_autorizadas(client):
    usuario = Usuario.objects.create_user(username="comissoes", password="teste")
    seed_groups()
    usuario.groups.add(Group.objects.get(name="Gestão de Comissões"))
    client.force_login(usuario)

    resposta = client.get(reverse("cadastros:central"))
    conteudo = resposta.content.decode()

    assert resposta.status_code == 200
    assert "Comissões" in conteudo
    assert "Pessoas e acessos" in conteudo
    assert "Pontuação" not in conteudo
    assert client.get(reverse("cadastros:area", args=["pontuacao"])).status_code == 403


@pytest.mark.django_db
def test_grid_pesquisa_filtra_ordena_e_responde_parcial(client, staff_user):
    hoje = timezone.localdate()
    Comissao.objects.create(
        nome="Comissão antiga",
        sigla="ANT",
        inicio_vigencia=hoje - timedelta(days=800),
        fim_vigencia=hoje - timedelta(days=100),
        ativa=False,
    )
    Comissao.objects.create(
        nome="Comissão vigente",
        sigla="CRSC",
        inicio_vigencia=hoje - timedelta(days=10),
        ativa=True,
    )
    client.force_login(staff_user)

    resposta = client.get(
        reverse("cadastros:lista", args=["comissoes"]),
        {"q": "vigente", "ativa": "1", "ordering": "nome", "partial": "1"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    conteudo = resposta.content.decode()

    assert resposta.status_code == 200
    assert "Comissão vigente" in conteudo
    assert "Comissão antiga" not in conteudo
    assert "<!doctype html>" not in conteudo
    assert "data-grid-fragment" in conteudo


@pytest.mark.django_db
def test_crud_generico_registra_auditoria(client, staff_user):
    client.force_login(staff_user)
    hoje = timezone.localdate()

    resposta = client.post(
        reverse("cadastros:criar", args=["comissoes"]),
        {
            "nome": "Comissão cadastrada pela interface",
            "sigla": "CRSC",
            "ato_designacao": "Portaria 100/2026",
            "inicio_vigencia": hoje.isoformat(),
            "fim_vigencia": "",
            "ativa": "on",
            "observacoes": "Cadastro operacional.",
        },
    )

    assert resposta.status_code == 302
    comissao = Comissao.objects.get(nome="Comissão cadastrada pela interface")
    assert comissao.created_by == staff_user
    assert comissao.updated_by == staff_user

    resposta = client.post(
        reverse("cadastros:editar", args=["comissoes", comissao.uuid]),
        {
            "nome": "Comissão atualizada",
            "sigla": "CRSC",
            "ato_designacao": "Portaria 100/2026",
            "inicio_vigencia": hoje.isoformat(),
            "fim_vigencia": "",
            "ativa": "on",
            "observacoes": "Atualizada.",
        },
    )
    assert resposta.status_code == 302
    comissao.refresh_from_db()
    assert comissao.nome == "Comissão atualizada"
    assert comissao.updated_by == staff_user


@pytest.mark.django_db
def test_cadastros_sincronizados_sao_somente_consulta(client, staff_user):
    client.force_login(staff_user)

    resposta = client.get(reverse("cadastros:criar", args=["vinculos"]))

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_requerente_visualiza_somente_os_proprios_requerimentos(client):
    usuario = Usuario.objects.create_user(username="proprietario", password="teste")
    outro = Usuario.objects.create_user(username="outro", password="teste")
    pessoa = PessoaInstitucional.objects.create(id_institucional=501, nome="Proprietário")
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual="Proprietário")
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=601,
        siape="1111111",
    )
    pessoa_outro = PessoaInstitucional.objects.create(id_institucional=502, nome="Outro")
    servidor_outro = Servidor.objects.create(pessoa=pessoa_outro, nome_atual="Outro")
    vinculo_outro = VinculoFuncional.objects.create(
        servidor=servidor_outro,
        id_servidor_externo=602,
        siape="2222222",
    )
    nivel = NivelRSC.objects.create(
        codigo="I",
        nome="RSC I",
        pontuacao_minima=Decimal("0"),
        quantidade_minima_itens=0,
    )
    proprio = Requerimento.objects.create(
        requerente=usuario,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )
    alheio = Requerimento.objects.create(
        requerente=outro,
        vinculo=vinculo_outro,
        nivel_pretendido=nivel,
    )
    client.force_login(usuario)

    resposta = client.get(reverse("requerimentos:lista"))
    conteudo = resposta.content.decode()

    assert resposta.status_code == 200
    assert proprio.numero in conteudo
    assert alheio.numero not in conteudo


@pytest.mark.django_db
def test_permissao_direta_residual_nao_libera_central(client):
    usuario = Usuario.objects.create_user(username="pontuacao", password="teste")
    permission = Permission.objects.get(
        content_type__app_label="pontuacao",
        codename="view_nivelrsc",
    )
    usuario.user_permissions.add(permission)
    client.force_login(usuario)

    assert client.get(reverse("cadastros:central")).status_code == 403
    assert client.get(reverse("cadastros:lista", args=["niveis-rsc"])).status_code == 403


@pytest.mark.django_db
def test_staff_sem_perfil_funcional_nao_acessa_cadastros(client):
    usuario = Usuario.objects.create_user(
        username="staff-tecnico",
        password="teste",
        is_staff=True,
    )
    client.force_login(usuario)

    assert client.get(reverse("cadastros:central")).status_code == 403
    assert client.get(reverse("cadastros:lista", args=["usuarios"])).status_code == 403


@pytest.mark.django_db
def test_operacao_de_triagem_nao_exibe_central_de_cadastros(client):
    seed_groups()
    usuario = Usuario.objects.create_user(username="operador", password="teste")
    usuario.groups.add(Group.objects.get(name="Operação de Triagem"))
    client.force_login(usuario)

    assert usuario.has_perm("comissoes.view_comissao")
    assert client.get(reverse("cadastros:central")).status_code == 403
    assert client.get(reverse("cadastros:lista", args=["comissoes"])).status_code == 403


@pytest.mark.django_db
def test_administrador_atribui_perfil_sem_usar_django_admin(client, staff_user):
    seed_groups()
    alvo = Usuario.objects.create_user(username="avaliador", password="teste")
    grupo = Group.objects.get(name="Gestão de Triagem")
    client.force_login(staff_user)

    resposta = client.post(
        reverse("cadastros:editar", args=["usuarios", alvo.uuid]),
        {"is_active": "on", "groups": [grupo.pk]},
    )

    assert resposta.status_code == 302
    alvo.refresh_from_db()
    assert alvo.is_active is True
    assert list(alvo.groups.values_list("name", flat=True)) == ["Gestão de Triagem"]
