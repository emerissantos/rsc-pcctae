from django.contrib import admin

from .models import EventoAuditoria, SessaoImpersonacao


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        "categoria",
        "tipo",
        "nivel",
        "ator",
        "usuario_afetado",
        "sucesso",
        "created_at",
    )
    list_filter = ("categoria", "tipo", "nivel", "sucesso", "created_at")
    search_fields = (
        "ator__username",
        "usuario_afetado__username",
        "descricao",
        "request_id",
        "objeto_tipo",
        "objeto_id",
        "caminho",
    )
    readonly_fields = tuple(field.name for field in EventoAuditoria._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SessaoImpersonacao)
class SessaoImpersonacaoAdmin(admin.ModelAdmin):
    list_display = ("ator", "usuario_simulado", "iniciada_em", "encerrada_em")
    list_filter = ("iniciada_em", "encerrada_em")
    search_fields = ("ator__username", "usuario_simulado__username", "justificativa")
    readonly_fields = tuple(field.name for field in SessaoImpersonacao._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
