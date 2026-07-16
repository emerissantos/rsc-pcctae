from django.urls import path

from . import views

app_name = "pontuacao"

urlpatterns = [path("", views.tabela, name="tabela")]
