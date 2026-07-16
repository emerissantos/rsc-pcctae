from django.urls import path

from . import views

app_name = "requerimentos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.criar, name="criar"),
    path("<uuid:uuid>/", views.detalhe, name="detalhe"),
    path("<uuid:uuid>/itens/", views.itens, name="itens"),
    path(
        "<uuid:uuid>/itens/<uuid:item_uuid>/upload/",
        views.upload_comprovante,
        name="upload-comprovante",
    ),
    path(
        "<uuid:uuid>/uploads/<uuid:upload_uuid>/remover/",
        views.remover_upload_temporario,
        name="remover-upload",
    ),
    path(
        "<uuid:uuid>/itens/<uuid:item_uuid>/salvar/",
        views.salvar_item,
        name="salvar-item",
    ),
    path(
        "<uuid:uuid>/itens/<uuid:item_uuid>/remover/",
        views.remover_item,
        name="remover-item",
    ),
    path(
        "<uuid:uuid>/documentos/<uuid:documento_uuid>/baixar/",
        views.baixar_documento,
        name="baixar-documento",
    ),
    path(
        "<uuid:uuid>/documentos/<uuid:documento_uuid>/remover/",
        views.remover_documento,
        name="remover-documento",
    ),
    path("<uuid:uuid>/revisao/", views.revisao, name="revisao"),
    path("<uuid:uuid>/submeter/", views.submeter, name="submeter"),
]
