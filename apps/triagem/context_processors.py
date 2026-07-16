from django.db.models import Q
from django.utils import timezone


def permissoes_triagem(request):
    usuario = getattr(request, "user", None)
    pode_acessar = False
    if usuario and usuario.is_authenticated:
        hoje = timezone.localdate()
        pode_acessar = usuario.is_staff or usuario.participacoes_comissoes.filter(
            ativo=True,
            inicio_mandato__lte=hoje,
            comissao__ativa=True,
            comissao__inicio_vigencia__lte=hoje,
        ).filter(
            Q(fim_mandato__isnull=True) | Q(fim_mandato__gte=hoje),
            Q(comissao__fim_vigencia__isnull=True) | Q(comissao__fim_vigencia__gte=hoje),
        ).exists()
    return {"pode_acessar_triagem": pode_acessar}
