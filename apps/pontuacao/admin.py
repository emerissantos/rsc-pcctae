from django.contrib import admin

from .models import ItemPontuacao, NivelRequisitoObrigatorio, NivelRSC, Requisito


class ItemInline(admin.TabularInline):
    model = ItemPontuacao
    extra = 0
    fields = (
        "codigo",
        "descricao",
        "unidade",
        "pontos_por_quantidade",
        "limite_pontos",
        "ativo",
    )
    show_change_link = True


@admin.register(Requisito)
class RequisitoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ordem", "ativo")
    list_editable = ("ordem", "ativo")
    search_fields = ("codigo", "nome", "descricao")
    inlines = (ItemInline,)


@admin.register(ItemPontuacao)
class ItemPontuacaoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "requisito",
        "pontos_por_quantidade",
        "unidade",
        "tipo_quantidade",
        "exige_anexo",
        "ativo",
    )
    list_filter = ("requisito", "tipo_quantidade", "exige_anexo", "ativo")
    search_fields = ("codigo", "descricao", "unidade")
    ordering = ("requisito__ordem", "ordem")


class NivelRequisitoInline(admin.TabularInline):
    model = NivelRequisitoObrigatorio
    extra = 0


@admin.register(NivelRSC)
class NivelRSCAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "pontuacao_minima",
        "quantidade_minima_itens",
        "ordem",
        "ativo",
    )
    list_editable = ("pontuacao_minima", "quantidade_minima_itens", "ordem", "ativo")
    inlines = (NivelRequisitoInline,)
