from django.urls import path

from . import views

app_name = "triagem"

urlpatterns = [
    path("", views.fila, name="fila"),
    path("<uuid:uuid>/iniciar/", views.iniciar, name="iniciar"),
    path("<uuid:uuid>/", views.detalhe, name="detalhe"),
    path("<uuid:uuid>/salvar/", views.salvar, name="salvar"),
    path("<uuid:uuid>/concluir/", views.concluir, name="concluir"),
]
