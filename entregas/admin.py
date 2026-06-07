from django.contrib import admin

from .models import Entrega, EventoEntrega, Motorista, MotivoInsucesso, Operador, Rota


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_controle",
        "cliente",
        "bairro",
        "motorista",
        "status",
        "volumes",
        "criado_em",
    )
    list_filter = ("status", "motorista", "pdv", "criado_em")
    search_fields = ("numero_controle", "cliente", "rua", "bairro", "motorista")
    ordering = ("-criado_em",)
    readonly_fields = ("numero_controle", "data_controle", "sequencia_controle")


@admin.register(Rota)
class RotaAdmin(admin.ModelAdmin):
    list_display = ("numero_rota", "motorista", "status", "total_entregas", "total_volumes", "saida_em")
    list_filter = ("status", "motorista", "saida_em")
    search_fields = ("numero_rota", "motorista", "responsavel_saida")
    readonly_fields = ("numero_rota", "data_rota", "sequencia_rota")


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "telefone")


@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(MotivoInsucesso)
class MotivoInsucessoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "permite_reagendamento", "ativo")
    list_filter = ("ativo", "permite_reagendamento")
    search_fields = ("descricao",)


@admin.register(EventoEntrega)
class EventoEntregaAdmin(admin.ModelAdmin):
    list_display = ("entrega", "tipo", "usuario", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("entrega__numero_controle", "descricao", "usuario")
    readonly_fields = ("entrega", "tipo", "descricao", "usuario", "criado_em")
