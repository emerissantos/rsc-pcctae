from django.contrib import admin

from .models import (
    ConfiguracaoTriagem,
    ItemChecklistTriagem,
    TriagemRequerimento,
    VerificacaoChecklistTriagem,
)


@admin.register(ConfiguracaoTriagem)
class ConfiguracaoTriagemAdmin(admin.ModelAdmin):
    list_display = ("prazo_correcao_dias", "updated_at")

    def has_add_permission(self, request):
        return not ConfiguracaoTriagem.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ItemChecklistTriagem)
class ItemChecklistTriagemAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "ordem", "obrigatorio", "confere_comprovantes", "ativo")
    list_filter = ("obrigatorio", "confere_comprovantes", "ativo")
    search_fields = ("codigo", "titulo", "descricao")
    ordering = ("ordem", "codigo")


class VerificacaoInline(admin.TabularInline):
    model = VerificacaoChecklistTriagem
    extra = 0
    readonly_fields = (
        "item",
        "item_codigo_snapshot",
        "item_titulo_snapshot",
        "item_descricao_snapshot",
        "item_obrigatorio_snapshot",
        "item_confere_comprovantes_snapshot",
    )


@admin.register(TriagemRequerimento)
class TriagemRequerimentoAdmin(admin.ModelAdmin):
    list_display = (
        "requerimento",
        "rodada",
        "responsavel",
        "resultado",
        "iniciada_em",
        "concluida_em",
        "prazo_correcao_ate",
    )
    list_filter = ("resultado", "iniciada_em")
    search_fields = ("requerimento__numero", "responsavel__username")
    readonly_fields = ("rodada", "iniciada_em", "concluida_em")
    inlines = (VerificacaoInline,)


@admin.register(VerificacaoChecklistTriagem)
class VerificacaoChecklistTriagemAdmin(admin.ModelAdmin):
    list_display = ("triagem", "item_codigo_snapshot", "situacao", "updated_at")
    list_filter = ("situacao", "item")
    search_fields = ("triagem__requerimento__numero", "item__codigo", "item__titulo")
