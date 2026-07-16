import pytest
from django.core.management import call_command

from apps.pontuacao.models import ItemPontuacao, NivelRSC, Requisito


@pytest.mark.django_db
def test_seed_e_idempotente():
    call_command("seed_rsc")
    call_command("seed_rsc")
    assert Requisito.objects.count() == 6
    assert ItemPontuacao.objects.count() == 57
    assert NivelRSC.objects.count() == 6
    assert ItemPontuacao.objects.filter(codigo="V.1-T", pontos_por_quantidade="9.00").exists()
    assert ItemPontuacao.objects.filter(codigo="V.1-S", pontos_por_quantidade="4.50").exists()
