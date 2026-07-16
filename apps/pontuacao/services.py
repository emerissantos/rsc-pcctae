from decimal import Decimal

from .models import ItemPontuacao


def calcular_pontuacao(item: ItemPontuacao, quantidade: Decimal | int | str) -> Decimal:
    """Calcula a pontuação exclusivamente a partir do item e da quantidade declarada."""
    return item.calcular(quantidade)
