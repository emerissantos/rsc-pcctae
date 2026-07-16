from django.contrib import admin

from .models import Comissao, MembroComissao


class MembroInline(admin.TabularInline):
    model = MembroComissao
    extra = 0
    fields = (
        "usuario",
        "nome_snapshot",
        "email_snapshot",
        "papel",
        "inicio_mandato",
        "fim_mandato",
        "ativo",
    )


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "sigla", "inicio_vigencia", "fim_vigencia", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome", "sigla", "ato_designacao")
    inlines = (MembroInline,)


@admin.register(MembroComissao)
class MembroComissaoAdmin(admin.ModelAdmin):
    list_display = ("nome_snapshot", "comissao", "papel", "inicio_mandato", "fim_mandato", "ativo")
    list_filter = ("comissao", "papel", "ativo")
    search_fields = ("nome_snapshot", "email_snapshot")
