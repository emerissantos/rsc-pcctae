from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.contas.models import IdentidadeExterna, Usuario
from apps.pessoas.models import PessoaInstitucional, Servidor, VinculoFuncional
from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito
from apps.requerimentos.models import (
    DocumentoLancamento,
    LancamentoItem,
    Requerimento,
    UploadTemporario,
)


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


@pytest.fixture
def requerimento_com_item(db):
    usuario = Usuario.objects.create_user(username="servidor2", password="teste")
    pessoa = PessoaInstitucional.objects.create(id_institucional=11, nome="Servidor Dois")
    IdentidadeExterna.objects.create(
        usuario=usuario,
        pessoa=pessoa,
        id_usuario_externo=2,
        id_institucional=11,
        login="servidor2",
    )
    servidor = Servidor.objects.create(pessoa=pessoa, nome_atual="Servidor Dois")
    vinculo = VinculoFuncional.objects.create(
        servidor=servidor,
        id_servidor_externo=21,
        siape="7654321",
        cargo_nome="Técnico",
    )
    nivel = NivelRSC.objects.create(
        codigo="II",
        nome="RSC II",
        pontuacao_minima=Decimal("15.00"),
        quantidade_minima_itens=1,
    )
    requisito = Requisito.objects.create(codigo="IV", nome="Requisito IV", ordem=4)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="IV.2",
        descricao="Item de teste",
        unidade="Por período",
        pontos_por_quantidade=Decimal("3.00"),
        tipo_quantidade=ItemPontuacao.TipoQuantidade.INTEIRA,
    )
    requerimento = Requerimento.objects.create(
        requerente=usuario,
        vinculo=vinculo,
        nivel_pretendido=nivel,
    )
    return usuario, requerimento, item


def enviar_upload(client, requerimento, item, arquivo):
    response = client.post(
        reverse("requerimentos:upload-comprovante", args=[requerimento.uuid, item.uuid]),
        {"arquivo": arquivo},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 201
    return response.json()["id"]


def salvar_com_uploads(client, requerimento, item, *, quantidade, arquivos, observacao=""):
    ids = [enviar_upload(client, requerimento, item, arquivo) for arquivo in arquivos]
    return client.post(
        reverse("requerimentos:salvar-item", args=[requerimento.uuid, item.uuid]),
        {"quantidade": quantidade, "observacao": observacao, "upload_ids": ids},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )


@pytest.mark.django_db
def test_salvar_item_aceita_varios_comprovantes(client, requerimento_com_item, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    response = salvar_com_uploads(
        client,
        requerimento,
        item,
        quantidade="2",
        observacao="Dois períodos comprovados.",
        arquivos=[
            SimpleUploadedFile("periodo-1.pdf", b"um", content_type="application/pdf"),
            SimpleUploadedFile("periodo-2.pdf", b"dois", content_type="application/pdf"),
        ],
    )

    assert response.status_code == 200
    lancamento = LancamentoItem.objects.get(requerimento=requerimento, item=item)
    assert lancamento.quantidade_declarada == Decimal("2")
    assert lancamento.documentos.count() == 2
    assert response.json()["documentos"] == 2


@pytest.mark.django_db
def test_salvar_item_inteiro_rejeita_fracao(client, requerimento_com_item):
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    response = client.post(
        reverse("requerimentos:salvar-item", args=[requerimento.uuid, item.uuid]),
        {
            "quantidade": "1.01",
            "documentos": SimpleUploadedFile(
                "comprovante.pdf", b"arquivo", content_type="application/pdf"
            ),
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 400
    assert "somente quantidade inteira" in response.json()["erro"]
    assert not LancamentoItem.objects.filter(requerimento=requerimento, item=item).exists()


@pytest.mark.django_db
def test_item_obrigatorio_exige_comprovante(client, requerimento_com_item):
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    response = client.post(
        reverse("requerimentos:salvar-item", args=[requerimento.uuid, item.uuid]),
        {"quantidade": "1"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 400
    assert "ao menos um comprovante" in response.json()["erro"]


@pytest.mark.django_db
def test_upload_temporario_so_vira_documento_apos_salvar(
    client, requerimento_com_item, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    upload_id = enviar_upload(
        client,
        requerimento,
        item,
        SimpleUploadedFile("temporario.pdf", b"temporario", content_type="application/pdf"),
    )
    assert UploadTemporario.objects.filter(uuid=upload_id, status="CONCLUIDO").exists()
    assert not DocumentoLancamento.objects.exists()
    response = client.post(
        reverse("requerimentos:salvar-item", args=[requerimento.uuid, item.uuid]),
        {"quantidade": "1", "upload_ids": [upload_id]},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert DocumentoLancamento.objects.count() == 1
    assert UploadTemporario.objects.get(uuid=upload_id).status == "VINCULADO"


@pytest.mark.django_db
def test_documento_so_e_entregue_por_endpoint_autenticado(
    client, requerimento_com_item, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    settings.RSC_USE_X_ACCEL_REDIRECT = False
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    salvar_com_uploads(
        client,
        requerimento,
        item,
        quantidade="2",
        arquivos=[
            SimpleUploadedFile(
                "periodos.pdf",
                b"conteudo-privado",
                content_type="application/pdf",
            )
        ],
    )
    documento = DocumentoLancamento.objects.get()

    resposta = client.get(
        reverse(
            "requerimentos:baixar-documento",
            args=[requerimento.uuid, documento.uuid],
        )
    )

    assert resposta.status_code == 200
    assert b"".join(resposta.streaming_content) == b"conteudo-privado"
    assert resposta["Cache-Control"] == "private, no-store, no-cache, max-age=0"
    assert "attachment" in resposta["Content-Disposition"]
    assert "Location" not in resposta

    # Não existe rota pública que sirva o caminho físico do arquivo.
    assert client.get(f"/media/{documento.arquivo.name}").status_code == 404
    assert client.get(f"/_private_files_not_public_/{documento.arquivo.name}").status_code == 404
    with pytest.raises(ValueError, match="não possuem URL pública"):
        _ = documento.arquivo.url


@pytest.mark.django_db
def test_outro_usuario_nao_acessa_documento(client, requerimento_com_item, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.RSC_USE_X_ACCEL_REDIRECT = False
    proprietario, requerimento, item = requerimento_com_item
    client.force_login(proprietario)
    salvar_com_uploads(
        client,
        requerimento,
        item,
        quantidade="1",
        arquivos=[SimpleUploadedFile("privado.pdf", b"segredo", content_type="application/pdf")],
    )
    documento = DocumentoLancamento.objects.get()

    outro = Usuario.objects.create_user(username="outro", password="teste")
    client.force_login(outro)
    resposta = client.get(
        reverse(
            "requerimentos:baixar-documento",
            args=[requerimento.uuid, documento.uuid],
        )
    )
    assert resposta.status_code == 403


@pytest.mark.django_db
def test_producao_autoriza_nginx_sem_expor_url_publica(
    client, requerimento_com_item, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    settings.RSC_USE_X_ACCEL_REDIRECT = True
    settings.RSC_PROTECTED_MEDIA_INTERNAL_URL = "/_protected_media/"
    usuario, requerimento, item = requerimento_com_item
    client.force_login(usuario)
    salvar_com_uploads(
        client,
        requerimento,
        item,
        quantidade="1",
        arquivos=[SimpleUploadedFile("interno.pdf", b"interno", content_type="application/pdf")],
    )
    documento = DocumentoLancamento.objects.get()

    resposta = client.get(
        reverse(
            "requerimentos:baixar-documento",
            args=[requerimento.uuid, documento.uuid],
        )
    )
    assert resposta.status_code == 200
    assert resposta["X-Accel-Redirect"].startswith("/_protected_media/requerimentos/")
    assert "Location" not in resposta
