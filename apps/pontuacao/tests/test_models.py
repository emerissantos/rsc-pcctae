from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.pontuacao.models import ItemPontuacao, Requisito


@pytest.mark.django_db
def test_calculo_por_item_e_quantidade():
    requisito = Requisito.objects.create(codigo="IV", nome="Requisito IV", ordem=4)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="IV.2",
        descricao="Elaboração de termo de referência",
        unidade="Por designação",
        pontos_por_quantidade=Decimal("3.00"),
        ordem=20,
    )
    assert item.calcular(3) == Decimal("9.00")


@pytest.mark.django_db
def test_item_inteiro_rejeita_quantidade_fracionada():
    requisito = Requisito.objects.create(codigo="I", nome="Requisito I", ordem=1)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="I.1",
        descricao="Participação",
        unidade="Por designação",
        pontos_por_quantidade=Decimal("3.00"),
    )
    with pytest.raises(ValidationError):
        item.calcular("1.5")


@pytest.mark.django_db
def test_limite_de_pontos_e_aplicado():
    requisito = Requisito.objects.create(codigo="II", nome="Requisito II", ordem=2)
    item = ItemPontuacao.objects.create(
        requisito=requisito,
        codigo="II.1",
        descricao="Projeto",
        unidade="Por projeto",
        pontos_por_quantidade=Decimal("7.50"),
        limite_pontos=Decimal("15.00"),
    )
    assert item.calcular(4) == Decimal("15.00")
