from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from .models import ItemPontuacao, NivelRSC, Requisito


@login_required
def tabela(request):
    requisitos = Requisito.objects.filter(ativo=True).prefetch_related(
        Prefetch("itens", queryset=ItemPontuacao.objects.filter(ativo=True))
    )
    niveis = NivelRSC.objects.filter(ativo=True).prefetch_related("requisitos_obrigatorios")
    return render(
        request,
        "pontuacao/tabela.html",
        {"requisitos": requisitos, "niveis": niveis},
    )
