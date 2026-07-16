from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import IdentidadeExterna, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    readonly_fields = ("uuid", "primeiro_acesso_em", "ultimo_acesso_em")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Dados institucionais locais",
            {"fields": ("uuid", "nome_exibicao", "primeiro_acesso_em", "ultimo_acesso_em")},
        ),
    )


@admin.register(IdentidadeExterna)
class IdentidadeExternaAdmin(admin.ModelAdmin):
    list_display = (
        "login",
        "provedor",
        "id_usuario_externo",
        "id_institucional",
        "ativo_na_origem",
        "ultima_sincronizacao_em",
    )
    search_fields = ("login", "nome_recebido", "email_recebido")
    list_filter = ("provedor", "ativo_na_origem")
    readonly_fields = ("created_at", "updated_at")
