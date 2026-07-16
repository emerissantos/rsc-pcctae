from django.contrib import admin

from .models import ExecucaoSincronizacao, PessoaInstitucional, Servidor, VinculoFuncional


@admin.register(PessoaInstitucional)
class PessoaInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("id_institucional", "nome", "email_institucional", "sincronizado_em")
    search_fields = ("nome", "email_institucional", "id_institucional")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("nome_atual", "email_atual", "ativo", "ultima_sincronizacao_em")
    search_fields = ("nome_atual", "email_atual", "pessoa__id_institucional")
    readonly_fields = ("created_at", "updated_at")


@admin.register(VinculoFuncional)
class VinculoFuncionalAdmin(admin.ModelAdmin):
    list_display = ("siape", "servidor", "cargo_nome", "lotacao_nome", "ativo")
    list_filter = ("ativo", "id_categoria_externa", "id_situacao_externa")
    search_fields = ("siape", "servidor__nome_atual", "cargo_nome", "lotacao_nome")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(ExecucaoSincronizacao)
class ExecucaoSincronizacaoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "id_institucional_consultado", "situacao", "iniciada_em")
    list_filter = ("tipo", "situacao")
    readonly_fields = [field.name for field in ExecucaoSincronizacao._meta.fields]
