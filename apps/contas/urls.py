from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.login, name="login"),
    path("oauth/iniciar/", views.oauth_start, name="oauth-start"),
    path("callback/", views.oauth_callback, name="oauth-callback"),
    path("sair/", views.logout, name="logout"),
]
