from django.contrib import admin

from .models import DocumentoLancamento, HistoricoRequerimento, LancamentoItem, Requerimento


class LancamentoInline(admin.TabularInline):
    model = LancamentoItem
    extra = 0
    readonly_fields = (
        "item_codigo_snapshot",
        "pontuacao_declarada",
        "item_pontos_snapshot",
    )


@admin.register(Requerimento)
class RequerimentoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "requerente",
        "vinculo",
        "nivel_pretendido",
        "situacao",
        "pontuacao_declarada",
        "submetido_em",
    )
    list_filter = ("situacao", "nivel_pretendido", "comissao")
    search_fields = (
        "numero",
        "requerente__username",
        "requerente__nome_exibicao",
        "vinculo__siape",
    )
    readonly_fields = ("numero", "pontuacao_declarada", "submetido_em", "finalizado_em")
    inlines = (LancamentoInline,)


@admin.register(LancamentoItem)
class LancamentoItemAdmin(admin.ModelAdmin):
    list_display = (
        "requerimento",
        "item_codigo_snapshot",
        "quantidade_declarada",
        "pontuacao_declarada",
        "situacao_validacao",
    )
    list_filter = ("situacao_validacao", "item__requisito")
    search_fields = ("requerimento__numero", "item_codigo_snapshot", "item_descricao_snapshot")


@admin.register(DocumentoLancamento)
class DocumentoLancamentoAdmin(admin.ModelAdmin):
    list_display = ("nome_original", "lancamento", "tamanho_bytes", "ativo", "created_at")
    search_fields = ("nome_original", "sha256", "lancamento__requerimento__numero")


@admin.register(HistoricoRequerimento)
class HistoricoRequerimentoAdmin(admin.ModelAdmin):
    list_display = ("requerimento", "situacao_nova", "created_at", "created_by")
    readonly_fields = (
        "requerimento",
        "situacao_anterior",
        "situacao_nova",
        "descricao",
        "created_at",
        "created_by",
    )
