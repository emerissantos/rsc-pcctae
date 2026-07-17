from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.comissoes.models import Comissao, MembroComissao
from apps.contas.models import Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.requerimentos.models import HistoricoRequerimento, LancamentoItem, Requerimento
from apps.triagem.models import (
    ConfiguracaoTriagem,
    ItemChecklistTriagem,
    TriagemRequerimento,
    VerificacaoChecklistTriagem,
)


def criar_usuario_com_vinculo(username: str):
    usuario = Usuario.objects.create_user(username=username, password="teste")
    pessoa = PessoaInstitucional.objects.create(
        id_institucional=1000 + Usuario.objects.count(),
        nome=f"Servidor {username}",
    )
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual=f"Servidor {username}")
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=2000 + Usuario.objects.count(),
        siape=f"{3000000 + Usuario.objects.count()}",
        cargo_nome="Técnico Administrativo",
    )
    return usuario, vinculo


@pytest.fixture
def contexto_triagem(db):
    hoje = timezone.localdate()
    requerente, vinculo = criar_usuario_com_vinculo("requerente")
    membro, _ = criar_usuario_com_vinculo("membro")
    nivel = NivelRSC.objects.create(
        codigo="I",
        nome="RSC I",
        pontuacao_minima=Decimal("0.00"),
        quantidade_minima_itens=0,
    )
    comissao = Comissao.objects.create(
        nome="Comissão RSC",
        sigla="CRSC",
        inicio_vigencia=hoje - timedelta(days=30),
        ativa=True,
    )
    MembroComissao.objects.create(
        comissao=comissao,
        usuario=membro,
        nome_snapshot=str(membro),
        papel=MembroComissao.Papel.MEMBRO,
        inicio_mandato=hoje - timedelta(days=10),
        ativo=True,
    )
    requerimento = Requerimento.objects.create(
        requerente=requerente,
        vinculo=vinculo,
        nivel_pretendido=nivel,
        comissao=comissao,
        situacao=Requerimento.Situacao.SUBMETIDO,
        submetido_em=timezone.now(),
    )
    ItemChecklistTriagem.objects.create(
        codigo="T-01",
        titulo="Identificação",
        ordem=1,
        obrigatorio=True,
    )
    ItemChecklistTriagem.objects.create(
        codigo="T-02",
        titulo="Comprovantes",
        ordem=2,
        obrigatorio=True,
        confere_comprovantes=True,
    )
    return {
        "requerente": requerente,
        "membro": membro,
        "comissao": comissao,
        "requerimento": requerimento,
    }


def post_checklist(triagem, *, nao_conforme=False, orientacao=""):
    data = {"orientacao_correcao": orientacao}
    for indice, verificacao in enumerate(triagem.verificacoes.select_related("item")):
        situacao = (
            VerificacaoChecklistTriagem.Situacao.NAO_CONFORME
            if nao_conforme and indice == 0
            else VerificacaoChecklistTriagem.Situacao.CONFORME
        )
        data[f"{verificacao.uuid}-situacao"] = situacao
        data[f"{verificacao.uuid}-observacao"] = (
            "Documento incompleto." if situacao.endswith("NAO_CONFORME") else ""
        )
    return data


@pytest.mark.django_db
def test_membro_da_comissao_inicia_triagem(client, contexto_triagem):
    client.force_login(contexto_triagem["membro"])
    requerimento = contexto_triagem["requerimento"]

    resposta = client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))

    assert resposta.status_code == 302
    requerimento.refresh_from_db()
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)
    assert requerimento.situacao == Requerimento.Situacao.EM_TRIAGEM
    assert triagem.responsavel == contexto_triagem["membro"]
    assert triagem.verificacoes.count() == 2
    assert HistoricoRequerimento.objects.filter(
        requerimento=requerimento,
        situacao_nova=Requerimento.Situacao.EM_TRIAGEM,
    ).exists()


@pytest.mark.django_db
def test_usuario_fora_da_comissao_nao_acessa_triagem(client, contexto_triagem):
    estranho = Usuario.objects.create_user(username="estranho", password="teste")
    client.force_login(estranho)

    resposta = client.get(reverse("triagem:fila"))

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_triagem_conforme_encaminha_para_analise(client, contexto_triagem):
    client.force_login(contexto_triagem["membro"])
    requerimento = contexto_triagem["requerimento"]
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)

    resposta = client.post(
        reverse("triagem:concluir", args=[triagem.uuid]),
        post_checklist(triagem),
    )

    assert resposta.status_code == 302
    triagem.refresh_from_db()
    requerimento.refresh_from_db()
    assert triagem.resultado == TriagemRequerimento.Resultado.APTO
    assert triagem.concluida_em is not None
    assert requerimento.situacao == Requerimento.Situacao.EM_ANALISE


@pytest.mark.django_db
def test_triagem_com_pendencia_aplica_prazo_configurado(client, contexto_triagem):
    client.force_login(contexto_triagem["membro"])
    requerimento = contexto_triagem["requerimento"]
    ConfiguracaoTriagem.objects.create(prazo_correcao_dias=10)
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)

    resposta = client.post(
        reverse("triagem:concluir", args=[triagem.uuid]),
        post_checklist(
            triagem,
            nao_conforme=True,
            orientacao="Substitua o documento incompleto e submeta novamente.",
        ),
    )

    assert resposta.status_code == 302
    triagem.refresh_from_db()
    requerimento.refresh_from_db()
    assert triagem.resultado == TriagemRequerimento.Resultado.PENDENCIA
    assert triagem.prazo_correcao_dias_snapshot == 10
    assert triagem.prazo_correcao_ate == timezone.localdate() + timedelta(days=10)
    assert requerimento.situacao == Requerimento.Situacao.PENDENTE_CORRECAO


@pytest.mark.django_db
def test_pendencia_sem_orientacao_nao_conclui(client, contexto_triagem):
    client.force_login(contexto_triagem["membro"])
    requerimento = contexto_triagem["requerimento"]
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)

    resposta = client.post(
        reverse("triagem:concluir", args=[triagem.uuid]),
        post_checklist(triagem, nao_conforme=True, orientacao=""),
    )

    assert resposta.status_code == 302
    triagem.refresh_from_db()
    requerimento.refresh_from_db()
    assert triagem.resultado == TriagemRequerimento.Resultado.EM_ANDAMENTO
    assert requerimento.situacao == Requerimento.Situacao.EM_TRIAGEM


@pytest.mark.django_db
def test_correcao_resubmetida_preserva_situacao_anterior_e_comissao(db):
    hoje = timezone.localdate()
    requerente, vinculo = criar_usuario_com_vinculo("corrige")
    nivel = NivelRSC.objects.create(
        codigo="II",
        nome="RSC II",
        pontuacao_minima=Decimal("1.00"),
        quantidade_minima_itens=1,
    )
    requisito = Requisito.objects.create(codigo="I", nome="Requisito I", ordem=1)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="I.1",
        descricao="Item sem anexo",
        unidade="atividade",
        pontos_por_quantidade=Decimal("1.00"),
        exige_anexo=False,
    )
    comissao = Comissao.objects.create(
        nome="Comissão atual",
        inicio_vigencia=hoje - timedelta(days=1),
        ativa=True,
    )
    requerimento = Requerimento.objects.create(
        requerente=requerente,
        vinculo=vinculo,
        nivel_pretendido=nivel,
        comissao=comissao,
        situacao=Requerimento.Situacao.PENDENTE_CORRECAO,
    )
    LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=Decimal("1"),
    )

    requerimento.submeter(requerente)

    requerimento.refresh_from_db()
    historico = requerimento.historico.latest("created_at")
    assert requerimento.situacao == Requerimento.Situacao.SUBMETIDO
    assert requerimento.comissao == comissao
    assert historico.situacao_anterior == Requerimento.Situacao.PENDENTE_CORRECAO
    assert "Correções submetidas" in historico.descricao


@pytest.mark.django_db
def test_submissao_associa_comissao_vigente_automaticamente(db):
    hoje = timezone.localdate()
    requerente, vinculo = criar_usuario_com_vinculo("nova-submissao")
    nivel = NivelRSC.objects.create(
        codigo="III",
        nome="RSC III",
        pontuacao_minima=Decimal("1.00"),
        quantidade_minima_itens=1,
    )
    requisito = Requisito.objects.create(codigo="II", nome="Requisito II", ordem=2)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="II.1",
        descricao="Item para submissão",
        unidade="atividade",
        pontos_por_quantidade=Decimal("1.00"),
        exige_anexo=False,
    )
    comissao_antiga = Comissao.objects.create(
        nome="Comissão antiga",
        inicio_vigencia=hoje - timedelta(days=100),
        fim_vigencia=hoje - timedelta(days=1),
        ativa=True,
    )
    comissao_atual = Comissao.objects.create(
        nome="Comissão vigente",
        inicio_vigencia=hoje - timedelta(days=10),
        ativa=True,
    )
    requerimento = Requerimento.objects.create(
        requerente=requerente,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )
    LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=Decimal("1"),
    )

    requerimento.submeter(requerente)

    requerimento.refresh_from_db()
    assert requerimento.comissao == comissao_atual
    assert requerimento.comissao != comissao_antiga


@pytest.mark.django_db
def test_mandato_encerrado_nao_autoriza_fila(client, contexto_triagem):
    membro = contexto_triagem["membro"]
    participacao = membro.participacoes_comissoes.get(comissao=contexto_triagem["comissao"])
    participacao.fim_mandato = timezone.localdate() - timedelta(days=1)
    participacao.save()
    client.force_login(membro)

    resposta = client.get(reverse("triagem:fila"))

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_staff_com_participacao_inativa_nao_ve_menu_nem_fila(client, contexto_triagem):
    from django.test import RequestFactory

    from apps.triagem.context_processors import permissoes_triagem

    membro = contexto_triagem["membro"]
    membro.is_staff = True
    membro.save(update_fields=["is_staff"])
    participacao = membro.participacoes_comissoes.get(comissao=contexto_triagem["comissao"])
    participacao.ativo = False
    participacao.save(update_fields=["ativo", "updated_at"])

    request = RequestFactory().get("/")
    request.user = membro
    assert permissoes_triagem(request)["pode_acessar_triagem"] is False

    client.force_login(membro)
    assert client.get(reverse("triagem:fila")).status_code == 403


@pytest.mark.django_db
def test_staff_inativo_nao_acessa_triagem_nem_requerimento_por_url(client, contexto_triagem):
    membro = contexto_triagem["membro"]
    requerimento = contexto_triagem["requerimento"]
    client.force_login(membro)
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)

    membro.is_staff = True
    membro.save(update_fields=["is_staff"])
    participacao = membro.participacoes_comissoes.get(comissao=contexto_triagem["comissao"])
    participacao.ativo = False
    participacao.save(update_fields=["ativo", "updated_at"])

    assert client.get(reverse("triagem:detalhe", args=[triagem.uuid])).status_code == 403
    assert client.get(reverse("requerimentos:detalhe", args=[requerimento.uuid])).status_code == 403


@pytest.mark.django_db
def test_gestao_de_triagem_nao_concede_operacao(client, contexto_triagem):
    from django.contrib.auth.models import Group

    from apps.cadastros.permissions import seed_groups

    seed_groups()
    gestor = Usuario.objects.create_user(username="gestor-checklist", password="teste")
    gestor.groups.add(Group.objects.get(name="Gestão de Triagem"))
    client.force_login(gestor)

    assert client.get(reverse("triagem:fila")).status_code == 403


@pytest.mark.django_db
def test_operacao_de_triagem_concede_acesso_explicito(client, contexto_triagem):
    from django.contrib.auth.models import Group

    from apps.cadastros.permissions import seed_groups

    seed_groups()
    operador = Usuario.objects.create_user(username="operador-triagem", password="teste")
    operador.groups.add(Group.objects.get(name="Operação de Triagem"))
    client.force_login(operador)

    assert client.get(reverse("triagem:fila")).status_code == 200
    resposta = client.post(reverse("triagem:iniciar", args=[contexto_triagem["requerimento"].uuid]))
    assert resposta.status_code == 302
    assert TriagemRequerimento.objects.filter(
        requerimento=contexto_triagem["requerimento"], responsavel=operador
    ).exists()


@pytest.mark.django_db
def test_permissao_de_fila_sozinha_nao_permite_iniciar(client, contexto_triagem):
    from django.contrib.auth.models import Permission

    operador = Usuario.objects.create_user(username="consulta-triagem", password="teste")
    operador.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="triagem",
            codename="acessar_fila_triagem",
        )
    )
    client.force_login(operador)

    assert client.get(reverse("triagem:fila")).status_code == 200
    resposta = client.post(reverse("triagem:iniciar", args=[contexto_triagem["requerimento"].uuid]))
    assert resposta.status_code == 403
    assert not TriagemRequerimento.objects.filter(
        requerimento=contexto_triagem["requerimento"]
    ).exists()


@pytest.mark.django_db
def test_requerente_visualiza_historico_e_observacoes_da_triagem(client, contexto_triagem):
    requerimento = contexto_triagem["requerimento"]
    membro = contexto_triagem["membro"]
    client.force_login(membro)
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)
    client.post(
        reverse("triagem:concluir", args=[triagem.uuid]),
        post_checklist(
            triagem,
            nao_conforme=True,
            orientacao="Substitua o documento incompleto e submeta novamente.",
        ),
    )

    client.force_login(contexto_triagem["requerente"])
    resposta = client.get(reverse("requerimentos:detalhe", args=[requerimento.uuid]))

    assert resposta.status_code == 200
    assert "Correções solicitadas pela comissão" in resposta.content.decode()
    assert "Substitua o documento incompleto" in resposta.content.decode()
    assert "Documento incompleto." in resposta.content.decode()
    assert str(membro) in resposta.content.decode()
    assert "Rodada 1" in resposta.content.decode()
    assert "Concluída por" in resposta.content.decode()


@pytest.mark.django_db
def test_requerente_nao_visualiza_observacao_de_triagem_em_andamento(client, contexto_triagem):
    requerimento = contexto_triagem["requerimento"]
    client.force_login(contexto_triagem["membro"])
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)
    client.post(
        reverse("triagem:salvar", args=[triagem.uuid]),
        post_checklist(
            triagem,
            nao_conforme=True,
            orientacao="Rascunho interno que ainda não foi comunicado.",
        ),
    )

    client.force_login(contexto_triagem["requerente"])
    resposta = client.get(reverse("requerimentos:detalhe", args=[requerimento.uuid]))

    assert resposta.status_code == 200
    assert "Rascunho interno que ainda não foi comunicado." not in resposta.content.decode()
    assert "Documento incompleto." not in resposta.content.decode()


@pytest.mark.django_db
def test_comissao_visualiza_rodadas_anteriores_na_nova_triagem(client, contexto_triagem):
    requerimento = contexto_triagem["requerimento"]
    membro = contexto_triagem["membro"]
    client.force_login(membro)
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    primeira = TriagemRequerimento.objects.get(requerimento=requerimento)
    client.post(
        reverse("triagem:concluir", args=[primeira.uuid]),
        post_checklist(
            primeira,
            nao_conforme=True,
            orientacao="Orientação preservada da primeira rodada.",
        ),
    )

    requerimento.refresh_from_db()
    requisito = Requisito.objects.create(codigo="H", nome="Histórico", ordem=99)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="H.1",
        descricao="Item para nova submissão",
        unidade="atividade",
        pontos_por_quantidade=Decimal("1.00"),
        exige_anexo=False,
    )
    LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=Decimal("1"),
    )
    requerimento.refresh_from_db()
    requerimento.submeter(contexto_triagem["requerente"])
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    segunda = TriagemRequerimento.objects.get(requerimento=requerimento, rodada=2)

    resposta = client.get(reverse("triagem:detalhe", args=[segunda.uuid]))

    assert resposta.status_code == 200
    conteudo = resposta.content.decode()
    assert "Rodada 2" in conteudo
    assert "Rodada 1" in conteudo
    assert "Orientação preservada da primeira rodada." in conteudo


@pytest.mark.django_db
def test_requerente_membro_ativo_nao_ve_proprio_requerimento_na_fila(
    client, contexto_triagem
):
    hoje = timezone.localdate()
    requerente = contexto_triagem["requerente"]
    requerimento = contexto_triagem["requerimento"]
    MembroComissao.objects.create(
        comissao=contexto_triagem["comissao"],
        usuario=requerente,
        nome_snapshot=str(requerente),
        papel=MembroComissao.Papel.MEMBRO,
        inicio_mandato=hoje - timedelta(days=1),
        ativo=True,
    )
    client.force_login(requerente)

    resposta = client.get(reverse("triagem:fila"))

    assert resposta.status_code == 200
    assert requerimento.numero not in resposta.content.decode()


@pytest.mark.django_db
def test_requerente_membro_ativo_nao_inicia_triagem_do_proprio_requerimento(
    client, contexto_triagem
):
    hoje = timezone.localdate()
    requerente = contexto_triagem["requerente"]
    requerimento = contexto_triagem["requerimento"]
    MembroComissao.objects.create(
        comissao=contexto_triagem["comissao"],
        usuario=requerente,
        nome_snapshot=str(requerente),
        papel=MembroComissao.Papel.MEMBRO,
        inicio_mandato=hoje - timedelta(days=1),
        ativo=True,
    )
    client.force_login(requerente)

    resposta = client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))

    assert resposta.status_code == 403
    assert not TriagemRequerimento.objects.filter(requerimento=requerimento).exists()
    requerimento.refresh_from_db()
    assert requerimento.situacao == Requerimento.Situacao.SUBMETIDO


@pytest.mark.django_db
def test_requerente_com_permissoes_operacionais_nao_tria_proprio_requerimento(
    client, contexto_triagem
):
    from django.contrib.auth.models import Group

    from apps.cadastros.permissions import seed_groups

    seed_groups()
    requerente = contexto_triagem["requerente"]
    requerimento = contexto_triagem["requerimento"]
    requerente.groups.add(Group.objects.get(name="Operação de Triagem"))
    client.force_login(requerente)

    assert client.get(reverse("triagem:fila")).status_code == 200
    resposta = client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))

    assert resposta.status_code == 403
    assert not TriagemRequerimento.objects.filter(requerimento=requerimento).exists()


@pytest.mark.django_db
def test_requerente_superusuario_nao_tria_proprio_requerimento(client, contexto_triagem):
    requerente = contexto_triagem["requerente"]
    requerimento = contexto_triagem["requerimento"]
    requerente.is_staff = True
    requerente.is_superuser = True
    requerente.save(update_fields=["is_staff", "is_superuser"])
    client.force_login(requerente)

    resposta = client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))

    assert resposta.status_code == 403
    assert not TriagemRequerimento.objects.filter(requerimento=requerimento).exists()


@pytest.mark.django_db
def test_requerente_nao_acessa_nem_altera_triagem_propria_ja_iniciada(
    client, contexto_triagem
):
    from django.contrib.auth.models import Group

    from apps.cadastros.permissions import seed_groups

    requerimento = contexto_triagem["requerimento"]
    client.force_login(contexto_triagem["membro"])
    client.post(reverse("triagem:iniciar", args=[requerimento.uuid]))
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)

    seed_groups()
    requerente = contexto_triagem["requerente"]
    requerente.groups.add(Group.objects.get(name="Operação de Triagem"))
    client.force_login(requerente)

    assert client.get(reverse("triagem:detalhe", args=[triagem.uuid])).status_code == 403
    assert (
        client.post(
            reverse("triagem:salvar", args=[triagem.uuid]),
            post_checklist(triagem),
        ).status_code
        == 403
    )
    assert (
        client.post(
            reverse("triagem:concluir", args=[triagem.uuid]),
            post_checklist(triagem),
        ).status_code
        == 403
    )

    triagem.refresh_from_db()
    requerimento.refresh_from_db()
    assert triagem.resultado == TriagemRequerimento.Resultado.EM_ANDAMENTO
    assert requerimento.situacao == Requerimento.Situacao.EM_TRIAGEM
