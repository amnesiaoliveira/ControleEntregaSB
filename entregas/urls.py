from django.urls import path

from . import views


app_name = "entregas"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("controle/", views.controle_entregas, name="controle"),
    path("nova/", views.criar_entrega, name="criar"),
    path("entrega/<int:pk>/", views.detalhe_entrega, name="detalhe"),
    path("entrega/<int:pk>/editar/", views.editar_entrega, name="editar"),
    path("entrega/<int:pk>/status/<str:status>/", views.atualizar_status, name="status"),
    path("entrega/<int:pk>/fechar/", views.fechar_entrega, name="fechar_entrega"),
    path("rotas/", views.listar_rotas, name="rotas"),
    path("rotas/nova/", views.criar_rota, name="rota_criar"),
    path("rotas/<int:pk>/", views.detalhe_rota, name="rota_detalhe"),
    path("rotas/<int:pk>/imprimir/", views.imprimir_rota, name="rota_imprimir"),
    path("rotas/<int:pk>/retorno/", views.registrar_retorno_rota, name="rota_retorno"),
    path("cadastros/", views.cadastros_operacionais, name="cadastros"),
    path("relatorio/", views.relatorio_entregas, name="relatorio"),
]
