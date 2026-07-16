from django.urls import path

from . import views

app_name = "cadastros"

urlpatterns = [
    path("", views.central, name="central"),
    path("areas/<slug:area_slug>/", views.area, name="area"),
    path("<slug:resource_slug>/", views.lista, name="lista"),
    path("<slug:resource_slug>/novo/", views.criar, name="criar"),
    path("<slug:resource_slug>/<str:object_id>/editar/", views.editar, name="editar"),
    path("<slug:resource_slug>/<str:object_id>/excluir/", views.excluir, name="excluir"),
]
