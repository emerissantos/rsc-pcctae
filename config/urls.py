from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("autenticacao/", include("apps.contas.urls")),
    path("pontuacao/", include("apps.pontuacao.urls")),
    path("requerimentos/", include("apps.requerimentos.urls")),
    path("triagem/", include("apps.triagem.urls")),
    path("cadastros/", include("apps.cadastros.urls")),
]

# Arquivos enviados pelos usuários são privados. Eles nunca são expostos por
# MEDIA_URL, nem mesmo em desenvolvimento. O acesso ocorre exclusivamente por
# views autenticadas do app requerimentos.

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
