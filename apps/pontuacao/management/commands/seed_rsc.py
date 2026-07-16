from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.pontuacao.models import (
    ItemPontuacao,
    NivelRequisitoObrigatorio,
    NivelRSC,
    Requisito,
)
from apps.pontuacao.seed_data import ITENS, NIVEIS, REQUISITOS


class Command(BaseCommand):
    help = "Cria ou atualiza requisitos, itens e níveis do RSC-PCCTAE."

    @transaction.atomic
    def handle(self, *args, **options):
        requisitos = {}
        for data in REQUISITOS:
            obj, _ = Requisito.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nome": data["nome"],
                    "descricao": data["descricao"],
                    "ordem": data["ordem"],
                    "ativo": True,
                },
            )
            requisitos[obj.codigo] = obj

        for data in ITENS:
            ItemPontuacao.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "requisito": requisitos[data["requisito"]],
                    "descricao": data["descricao"],
                    "unidade": data["unidade"],
                    "pontos_por_quantidade": Decimal(data["pontos"]),
                    "tipo_quantidade": ItemPontuacao.TipoQuantidade.INTEIRA,
                    "exige_anexo": True,
                    "observacao_permitida": True,
                    "orientacao": (
                        "Informe a quantidade computável conforme a unidade do item e "
                        "anexe o documento comprobatório."
                    ),
                    "ordem": data["ordem"],
                    "ativo": True,
                },
            )

        for data in NIVEIS:
            nivel, _ = NivelRSC.objects.update_or_create(
                codigo=data["codigo"],
                defaults={
                    "nome": data["nome"],
                    "descricao": data["descricao"],
                    "pontuacao_minima": Decimal(data["pontuacao_minima"]),
                    "quantidade_minima_itens": data["quantidade_minima_itens"],
                    "ordem": data["ordem"],
                    "ativo": True,
                },
            )
            NivelRequisitoObrigatorio.objects.filter(nivel=nivel).delete()
            NivelRequisitoObrigatorio.objects.bulk_create(
                [
                    NivelRequisitoObrigatorio(
                        nivel=nivel,
                        requisito=requisitos[codigo],
                    )
                    for codigo in data["requisitos_obrigatorios"]
                ]
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed concluída: "
                f"{len(REQUISITOS)} requisitos, {len(ITENS)} itens e {len(NIVEIS)} níveis."
            )
        )
