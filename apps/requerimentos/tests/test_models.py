from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.contas.models import Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.requerimentos.models import DocumentoLancamento, LancamentoItem, Requerimento


@pytest.fixture
def dados_basicos(db):
    usuario = Usuario.objects.create_user(username="servidor", password="teste")
    pessoa = PessoaInstitucional.objects.create(id_institucional=10, nome="Servidor Teste")
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual="Servidor Teste")
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=20,
        siape="1234567",
        cargo_nome="Técnico",
    )
    nivel = NivelRSC.objects.create(
        codigo="IV",
        nome="RSC IV",
        pontuacao_minima=Decimal("30.00"),
        quantidade_minima_itens=1,
    )
    requisito = Requisito.objects.create(codigo="IV", nome="Requisito IV", ordem=4)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="IV.2",
        descricao="Elaboração de termo de referência",
        unidade="Por designação",
        pontos_por_quantidade=Decimal("3.00"),
    )
    requerimento = Requerimento.objects.create(
        requerente=usuario,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )
    return usuario, requerimento, item


@pytest.mark.django_db
def test_lancamento_calcula_e_preserva_snapshot(dados_basicos):
    usuario, requerimento, item = dados_basicos
    lancamento = LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=3,
        created_by=usuario,
        updated_by=usuario,
    )
    requerimento.refresh_from_db()
    assert lancamento.pontuacao_declarada == Decimal("9.00")
    assert lancamento.item_codigo_snapshot == "IV.2"
    assert requerimento.pontuacao_declarada == Decimal("9.00")


@pytest.mark.django_db
def test_submissao_com_anexo(dados_basicos):
    usuario, requerimento, item = dados_basicos
    lancamento = LancamentoItem.objects.create(
        requerimento=requerimento,
        item=item,
        quantidade_declarada=10,
        created_by=usuario,
        updated_by=usuario,
    )
    DocumentoLancamento.objects.create(
        lancamento=lancamento,
        arquivo=SimpleUploadedFile("comprovante.pdf", b"arquivo", content_type="application/pdf"),
        nome_original="comprovante.pdf",
        created_by=usuario,
        updated_by=usuario,
    )
    requerimento.submeter(usuario)
    requerimento.refresh_from_db()
    assert requerimento.situacao == Requerimento.Situacao.SUBMETIDO
    assert requerimento.submetido_em is not None
