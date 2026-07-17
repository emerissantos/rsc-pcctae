import time
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import normalizar_valor, snapshot_model
from apps.cadastros.permissions import seed_groups
from apps.comissoes.models import Comissao, MembroComissao
from apps.contas.models import Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.requerimentos.models import DocumentoLancamento, LancamentoItem, Requerimento
from apps.triagem.models import ItemChecklistTriagem, TriagemRequerimento


def criar_usuario_vinculo(username: str):
    usuario = Usuario.objects.create_user(username=username, password="segredo-teste")
    pessoa = PessoaInstitucional.objects.create(
        id_institucional=10000 + Usuario.objects.count(),
        nome=f"Servidor {username}",
    )
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual=pessoa.nome)
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=20000 + Usuario.objects.count(),
        siape=str(3000000 + Usuario.objects.count()),
    )
    return usuario, vinculo


def criar_requerimento(username="requerente-auditoria"):
    usuario, vinculo = criar_usuario_vinculo(username)
    nivel = NivelRSC.objects.create(
        codigo=f"N-{Usuario.objects.count()}",
        nome="Nível de teste",
        pontuacao_minima=Decimal("0"),
        quantidade_minima_itens=0,
    )
    requerimento = Requerimento.objects.create(
        requerente=usuario,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )
    return usuario, requerimento


@pytest.mark.django_db
def test_falha_oauth_e_registrada(client):
    session = client.session
    session["ufsb_oauth_flow"] = {
        "state": "esperado",
        "created_at": int(time.time()),
        "next": "/",
        "code_verifier": None,
    }
    session.save()

    resposta = client.get(
        reverse("contas:oauth-callback"),
        {"state": "outro", "code": "codigo"},
    )

    assert resposta.status_code == 302
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.LOGIN_FALHA)
    assert evento.categoria == EventoAuditoria.Categoria.AUTENTICACAO
    assert evento.sucesso is False
    assert evento.endereco_ip == "127.0.0.1"
    assert evento.dados["motivo"] == "state_invalido_ou_expirado"


@pytest.mark.django_db
def test_resposta_403_e_registrada_pelo_middleware(client):
    usuario = Usuario.objects.create_user(username="sem-perfil", password="teste")
    client.force_login(usuario)

    resposta = client.get(reverse("cadastros:central"))

    assert resposta.status_code == 403
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.ACESSO_NEGADO)
    assert evento.ator == usuario
    assert evento.status_http == 403
    assert evento.caminho == reverse("cadastros:central")
    assert evento.sucesso is False


@pytest.mark.django_db
def test_crud_cadastro_guarda_antes_depois_e_campos_alterados(client):
    seed_groups()
    gestor = Usuario.objects.create_user(username="gestor-audit", password="teste")
    gestor.groups.add(Group.objects.get(name="Administradores do RSC-PCCTAE"))
    hoje = timezone.localdate()
    client.force_login(gestor)
    comissao = Comissao.objects.create(
        nome="Comissão antes",
        sigla="AUD",
        inicio_vigencia=hoje,
        ativa=True,
    )

    resposta = client.post(
        reverse("cadastros:editar", args=["comissoes", comissao.uuid]),
        {
            "nome": "Comissão depois",
            "sigla": "AUD",
            "ato_designacao": "Portaria 1/2026",
            "inicio_vigencia": hoje.isoformat(),
            "fim_vigencia": "",
            "ativa": "on",
            "observacoes": "Alteração auditada",
        },
    )

    assert resposta.status_code == 302
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.CADASTRO_ALTERADO)
    assert evento.objeto_id == str(comissao.uuid)
    assert evento.dados_anteriores["nome"] == "Comissão antes"
    assert evento.dados_posteriores["nome"] == "Comissão depois"
    assert "nome" in evento.campos_alterados
    assert "observacoes" in evento.campos_alterados


@pytest.mark.django_db
def test_visualizacao_do_requerimento_e_auditada(client):
    usuario, requerimento = criar_requerimento()
    client.force_login(usuario)

    resposta = client.get(reverse("requerimentos:detalhe", args=[requerimento.uuid]))

    assert resposta.status_code == 200
    evento = EventoAuditoria.objects.get(
        tipo=EventoAuditoria.Tipo.REQUERIMENTO_VISUALIZADO
    )
    assert evento.ator == usuario
    assert evento.usuario_afetado == usuario
    assert evento.objeto_id == str(requerimento.uuid)
    assert evento.dados["como_requerente"] is True


@pytest.mark.django_db
def test_download_de_comprovante_e_auditado(client, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.RSC_USE_X_ACCEL_REDIRECT = False
    usuario, requerimento = criar_requerimento("download-audit")
    requisito = Requisito.objects.create(codigo="AUD", nome="Auditoria", ordem=1)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="AUD.1",
        descricao="Item",
        unidade="atividade",
        pontos_por_quantidade=Decimal("1"),
        exige_anexo=False,
    )
    lancamento = LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=Decimal("1"),
    )
    documento = DocumentoLancamento.objects.create(
        lancamento=lancamento,
        arquivo=SimpleUploadedFile("prova.pdf", b"conteudo", content_type="application/pdf"),
        nome_original="prova.pdf",
        tipo_mime="application/pdf",
    )
    client.force_login(usuario)

    resposta = client.get(
        reverse("requerimentos:baixar-documento", args=[requerimento.uuid, documento.uuid])
    )

    assert resposta.status_code == 200
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.DOCUMENTO_BAIXADO)
    assert evento.objeto_id == str(documento.uuid)
    assert evento.dados["requerimento"] == requerimento.numero


@pytest.mark.django_db
def test_inicio_e_conclusao_da_triagem_sao_auditados(client):
    hoje = timezone.localdate()
    requerente, requerimento = criar_requerimento("requerente-triagem-audit")
    membro, _ = criar_usuario_vinculo("membro-triagem-audit")
    comissao = Comissao.objects.create(
        nome="Comissão de auditoria",
        inicio_vigencia=hoje - timedelta(days=1),
        ativa=True,
    )
    MembroComissao.objects.create(
        comissao=comissao,
        usuario=membro,
        nome_snapshot=str(membro),
        papel=MembroComissao.Papel.MEMBRO,
        inicio_mandato=hoje - timedelta(days=1),
        ativo=True,
    )
    requerimento.comissao = comissao
    requerimento.situacao = Requerimento.Situacao.SUBMETIDO
    requerimento.submetido_em = timezone.now()
    requerimento.save(update_fields=["comissao", "situacao", "submetido_em", "updated_at"])
    ItemChecklistTriagem.objects.create(
        codigo="AUD-T1",
        titulo="Documento conferido",
        obrigatorio=True,
        ativo=True,
    )
    client.force_login(membro)

    assert client.post(reverse("triagem:iniciar", args=[requerimento.uuid])).status_code == 302
    triagem = TriagemRequerimento.objects.get(requerimento=requerimento)
    verificacao = triagem.verificacoes.get()
    resposta = client.post(
        reverse("triagem:concluir", args=[triagem.uuid]),
        {
            "orientacao_correcao": "",
            f"{verificacao.uuid}-situacao": "CONFORME",
            f"{verificacao.uuid}-observacao": "",
        },
    )

    assert resposta.status_code == 302
    assert EventoAuditoria.objects.filter(tipo=EventoAuditoria.Tipo.TRIAGEM_INICIADA).exists()
    evento = EventoAuditoria.objects.get(tipo=EventoAuditoria.Tipo.TRIAGEM_CONCLUIDA)
    assert evento.usuario_afetado == requerente
    assert evento.dados["resultado"] == "APTO"
    assert evento.dados["situacao_nova"] == Requerimento.Situacao.EM_ANALISE


@pytest.mark.django_db
def test_snapshot_nao_expoe_senha_e_mascara_cpf():
    usuario = Usuario.objects.create_user(username="protegido", password="senha-secreta")
    snapshot = snapshot_model(usuario)
    assert snapshot["password"] == "[PROTEGIDO]"
    assert "senha-secreta" not in str(snapshot)
    assert normalizar_valor("12345678900", field_name="cpf") == "***8900"


@pytest.mark.django_db
def test_detalhe_do_evento_exibe_comparacao_para_administrador(client):
    seed_groups()
    gestor = Usuario.objects.create_user(username="auditor", password="teste")
    gestor.groups.add(Group.objects.get(name="Administradores do RSC-PCCTAE"))
    evento = EventoAuditoria.objects.create(
        tipo=EventoAuditoria.Tipo.CADASTRO_ALTERADO,
        categoria=EventoAuditoria.Categoria.CADASTRO,
        ator=gestor,
        descricao="Alteração para conferência.",
        recurso="Comissões",
        objeto_tipo="comissoes.comissao",
        objeto_id="abc-123",
        dados_anteriores={"nome": "Antes"},
        dados_posteriores={"nome": "Depois"},
        campos_alterados=["nome"],
    )
    client.force_login(gestor)

    resposta = client.get(reverse("cadastros:evento-auditoria-detalhe", args=[evento.uuid]))
    conteudo = resposta.content.decode()

    assert resposta.status_code == 200
    assert "Alteração para conferência" in conteudo
    assert "Antes" in conteudo
    assert "Depois" in conteudo
    assert "abc-123" in conteudo
