import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    EntregaForm,
    FechamentoEntregaForm,
    MotivoInsucessoForm,
    MotoristaForm,
    OperadorForm,
    RelatorioFiltroForm,
    RetornoRotaForm,
    RotaForm,
)
from .models import Entrega, EventoEntrega, Motorista, MotivoInsucesso, Operador, Rota


def _usuario(request):
    return request.user.get_username() if request.user.is_authenticated else ""


def _registrar_evento(entrega, tipo, descricao, request=None):
    EventoEntrega.objects.create(
        entrega=entrega,
        tipo=tipo,
        descricao=descricao,
        usuario=_usuario(request) if request else "",
    )


def _dashboard_context(queryset=None):
    base = queryset if queryset is not None else Entrega.objects.all()
    hoje = timezone.localdate()
    entregas_hoje = base.filter(criado_em__date=hoje)
    abertas = base.exclude(status__in=[Entrega.Status.ENTREGUE, Entrega.Status.CANCELADA])

    return {
        "total_hoje": entregas_hoje.count(),
        "pendentes": base.filter(status=Entrega.Status.PENDENTE).count(),
        "em_rota": base.filter(status=Entrega.Status.EM_ROTA).count(),
        "rotas_ativas": Rota.objects.filter(status=Rota.Status.EM_ROTA).count(),
        "entregues_hoje": entregas_hoje.filter(status=Entrega.Status.ENTREGUE).count(),
        "atrasadas": abertas.filter(data_prevista__lt=hoje).count(),
        "volumes_pendentes": abertas.aggregate(total=Sum("volumes"))["total"] or 0,
    }


def _filtrar_entregas_relatorio(form):
    entregas = Entrega.objects.select_related("rota", "motivo_insucesso")

    if form.is_valid():
        data_inicio = form.cleaned_data.get("data_inicio")
        data_fim = form.cleaned_data.get("data_fim")
        motorista = form.cleaned_data.get("motorista")
        data_prevista = form.cleaned_data.get("data_prevista")
        status = form.cleaned_data.get("status")

        if data_inicio:
            entregas = entregas.filter(criado_em__date__gte=data_inicio)
        if data_fim:
            entregas = entregas.filter(criado_em__date__lte=data_fim)
        if motorista:
            entregas = entregas.filter(motorista__icontains=motorista)
        if data_prevista:
            entregas = entregas.filter(data_prevista=data_prevista)
        if status:
            entregas = entregas.filter(status=status)

    return entregas


@login_required
def dashboard(request):
    hoje = timezone.localdate()
    abertas = Entrega.objects.exclude(status__in=[Entrega.Status.ENTREGUE, Entrega.Status.CANCELADA])
    por_motorista = (
        abertas.values("motorista")
        .annotate(entregas=Count("id"), volumes=Sum("volumes"))
        .order_by("motorista")[:12]
    )
    rotas_ativas = Rota.objects.filter(status=Rota.Status.EM_ROTA).prefetch_related("entregas")[:8]

    return render(
        request,
        "entregas/dashboard.html",
        {
            **_dashboard_context(),
            "hoje": hoje,
            "por_motorista": por_motorista,
            "rotas_ativas_lista": rotas_ativas,
            "reagendadas": Entrega.objects.filter(status=Entrega.Status.REAGENDADA).order_by("reagendada_para")[:10],
            "atrasadas_lista": abertas.filter(data_prevista__lt=hoje).order_by("data_prevista")[:10],
        },
    )


@login_required
def controle_entregas(request):
    busca = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    entregas = Entrega.objects.select_related("rota", "motivo_insucesso")

    if busca:
        entregas = entregas.filter(
            Q(numero_controle__icontains=busca)
            | Q(cliente__icontains=busca)
            | Q(bairro__icontains=busca)
            | Q(motorista__icontains=busca)
            | Q(rota__numero_rota__icontains=busca)
        )

    if status:
        entregas = entregas.filter(status=status)

    context = {
        **_dashboard_context(),
        "entregas": entregas[:80],
        "busca": busca,
        "status_atual": status,
        "status_choices": Entrega.Status.choices,
    }
    return render(request, "entregas/controle.html", context)


@login_required
def criar_entrega(request):
    if request.method == "POST":
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save()
            _registrar_evento(entrega, EventoEntrega.Tipo.CRIADA, "Entrega lançada.", request)
            messages.success(request, "Entrega lançada com sucesso.")
            return redirect(entrega)
    else:
        form = EntregaForm()

    return render(
        request,
        "entregas/form.html",
        {
            "form": form,
            "titulo": "Lançar entrega",
            "proximo_numero_controle": Entrega.proximo_numero_controle(),
        },
    )


@login_required
def editar_entrega(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk)
    if request.method == "POST":
        form = EntregaForm(request.POST, instance=entrega)
        if form.is_valid():
            entrega = form.save()
            _registrar_evento(entrega, EventoEntrega.Tipo.EDITADA, "Dados da entrega atualizados.", request)
            messages.success(request, "Entrega atualizada com sucesso.")
            return redirect(entrega)
    else:
        form = EntregaForm(instance=entrega)

    return render(
        request,
        "entregas/form.html",
        {"form": form, "titulo": "Editar entrega", "entrega": entrega},
    )


@login_required
def detalhe_entrega(request, pk):
    entrega = get_object_or_404(
        Entrega.objects.select_related("rota", "motivo_insucesso").prefetch_related("eventos"),
        pk=pk,
    )
    fechamento_form = FechamentoEntregaForm()
    return render(
        request,
        "entregas/detalhe.html",
        {"entrega": entrega, "fechamento_form": fechamento_form},
    )


@login_required
def atualizar_status(request, pk, status):
    entrega = get_object_or_404(Entrega, pk=pk)
    status_validos = {choice[0] for choice in Entrega.Status.choices}

    if request.method == "POST" and status in status_validos:
        entrega.status = status
        entrega.save(update_fields=["status", "atualizado_em"])
        _registrar_evento(entrega, EventoEntrega.Tipo.STATUS, f"Status alterado para {entrega.get_status_display()}.", request)
        if entrega.rota:
            entrega.rota.atualizar_finalizacao()
        messages.success(request, "Status atualizado.")

    return redirect(request.POST.get("next") or entrega)


@login_required
def fechar_entrega(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk)
    if request.method == "POST":
        form = FechamentoEntregaForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data["status"]
            entrega.status = status
            entrega.motivo_insucesso = form.cleaned_data["motivo_insucesso"]
            entrega.reagendada_para = form.cleaned_data["reagendada_para"]
            entrega.recebedor_nome = form.cleaned_data["recebedor_nome"]
            entrega.recebedor_documento = form.cleaned_data["recebedor_documento"]
            entrega.comprovante_observacao = form.cleaned_data["comprovante_observacao"]
            campos = [
                "status",
                "motivo_insucesso",
                "reagendada_para",
                "recebedor_nome",
                "recebedor_documento",
                "comprovante_observacao",
                "atualizado_em",
            ]
            if status == Entrega.Status.REAGENDADA:
                entrega.data_prevista = entrega.reagendada_para
                entrega.rota = None
                campos.extend(["data_prevista", "rota"])
            entrega.save(update_fields=campos)
            _registrar_evento(entrega, EventoEntrega.Tipo.RETORNO, f"Fechamento registrado como {entrega.get_status_display()}.", request)
            if status == Entrega.Status.REAGENDADA:
                _registrar_evento(entrega, EventoEntrega.Tipo.REAGENDAMENTO, f"Entrega reagendada para {entrega.reagendada_para:%d/%m/%Y}.", request)
            if status == Entrega.Status.ENTREGUE:
                _registrar_evento(entrega, EventoEntrega.Tipo.COMPROVANTE, f"Recebido por {entrega.recebedor_nome}.", request)
            if entrega.rota:
                entrega.rota.atualizar_finalizacao()
            messages.success(request, "Fechamento registrado.")
        else:
            messages.error(request, "Revise os dados de fechamento.")
    return redirect(entrega)


@login_required
def relatorio_entregas(request):
    form = RelatorioFiltroForm(request.GET or None)
    entregas = _filtrar_entregas_relatorio(form)

    if request.GET.get("export") == "csv":
        return exportar_entregas_csv(entregas)

    status_labels = dict(Entrega.Status.choices)
    resumo_status = [
        {"status": status_labels[item["status"]], "total": item["total"]}
        for item in entregas.values("status").annotate(total=Count("id")).order_by("status")
    ]
    total_volumes = entregas.aggregate(total=Sum("volumes"))["total"] or 0

    return render(
        request,
        "entregas/relatorio.html",
        {
            "form": form,
            "entregas": entregas,
            "resumo_status": resumo_status,
            "total_entregas": entregas.count(),
            "total_volumes": total_volumes,
        },
    )


def exportar_entregas_csv(entregas):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="relatorio_entregas.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Controle",
            "Cliente",
            "Endereco",
            "Volumes",
            "PDV",
            "Operador",
            "Motorista",
            "Data prevista",
            "Rota",
            "Status",
            "Motivo",
        ]
    )
    for entrega in entregas:
        writer.writerow(
            [
                entrega.numero_controle,
                entrega.cliente,
                entrega.endereco_completo,
                entrega.volumes,
                entrega.pdv,
                entrega.operador,
                entrega.motorista,
                entrega.data_prevista,
                entrega.rota.numero_rota if entrega.rota else "",
                entrega.get_status_display(),
                entrega.motivo_insucesso.descricao if entrega.motivo_insucesso else "",
            ]
        )
    return response


@login_required
def listar_rotas(request):
    status = request.GET.get("status", "").strip()
    motorista = request.GET.get("motorista", "").strip()
    rotas = Rota.objects.prefetch_related("entregas")

    if status:
        rotas = rotas.filter(status=status)
    if motorista:
        rotas = rotas.filter(motorista__icontains=motorista)

    return render(
        request,
        "entregas/rotas.html",
        {
            "rotas": rotas,
            "status_atual": status,
            "motorista": motorista,
            "status_choices": Rota.Status.choices,
        },
    )


@login_required
def criar_rota(request):
    entregas_pendentes = Entrega.objects.filter(status=Entrega.Status.PENDENTE, rota__isnull=True)
    motorista_filtro = request.GET.get("motorista", "").strip()

    if motorista_filtro:
        entregas_pendentes = entregas_pendentes.filter(motorista__icontains=motorista_filtro)

    if request.method == "POST":
        form = RotaForm(request.POST)
        entrega_ids = request.POST.getlist("entregas")
        if form.is_valid() and entrega_ids:
            with transaction.atomic():
                entregas = list(
                    Entrega.objects.select_for_update().filter(
                        id__in=entrega_ids,
                        status=Entrega.Status.PENDENTE,
                        rota__isnull=True,
                    )
                )

                if not entregas:
                    messages.error(request, "Selecione entregas pendentes disponíveis para montar a rota.")
                    return redirect("entregas:rota_criar")

                rota = form.save()
                Entrega.objects.filter(id__in=[entrega.id for entrega in entregas]).update(
                    rota=rota,
                    motorista=rota.motorista,
                    motorista_cadastro=rota.motorista_cadastro,
                    status=Entrega.Status.EM_ROTA,
                    atualizado_em=timezone.now(),
                )
                for entrega in entregas:
                    _registrar_evento(entrega, EventoEntrega.Tipo.ROTA, f"Incluída na rota {rota.numero_rota}.", request)
                messages.success(request, f"Rota {rota.numero_rota} criada com {len(entregas)} entrega(s).")
                return redirect(rota)

        if not entrega_ids:
            messages.error(request, "Selecione pelo menos uma entrega para montar a rota.")
    else:
        form = RotaForm(initial={"motorista": motorista_filtro})

    motoristas_pendentes = (
        Entrega.objects.filter(status=Entrega.Status.PENDENTE, rota__isnull=True)
        .exclude(motorista="")
        .values_list("motorista", flat=True)
        .distinct()
        .order_by("motorista")
    )

    return render(
        request,
        "entregas/rota_form.html",
        {
            "form": form,
            "entregas": entregas_pendentes,
            "motoristas_pendentes": motoristas_pendentes,
            "motorista_filtro": motorista_filtro,
            "proximo_numero_rota": Rota.proximo_numero_rota(),
        },
    )


@login_required
def detalhe_rota(request, pk):
    rota = get_object_or_404(Rota.objects.prefetch_related("entregas"), pk=pk)
    retorno_form = RetornoRotaForm(initial={"observacoes_retorno": rota.observacoes_retorno})
    fechamento_form = FechamentoEntregaForm()
    return render(
        request,
        "entregas/rota_detalhe.html",
        {"rota": rota, "retorno_form": retorno_form, "fechamento_form": fechamento_form},
    )


@login_required
def imprimir_rota(request, pk):
    rota = get_object_or_404(Rota.objects.prefetch_related("entregas"), pk=pk)
    return render(request, "entregas/rota_impressao.html", {"rota": rota})


@login_required
def registrar_retorno_rota(request, pk):
    rota = get_object_or_404(Rota.objects.prefetch_related("entregas"), pk=pk)

    if request.method == "POST":
        retorno_form = RetornoRotaForm(request.POST)
        fechamento_form = FechamentoEntregaForm(request.POST)
        entrega_ids = request.POST.getlist("entregas")

        if retorno_form.is_valid():
            rota.observacoes_retorno = retorno_form.cleaned_data["observacoes_retorno"]
            rota.save(update_fields=["observacoes_retorno"])

        if entrega_ids and fechamento_form.is_valid():
            entregas = Entrega.objects.filter(id__in=entrega_ids, rota=rota)
            status = fechamento_form.cleaned_data["status"]
            for entrega in entregas:
                entrega.status = status
                entrega.motivo_insucesso = fechamento_form.cleaned_data["motivo_insucesso"]
                entrega.reagendada_para = fechamento_form.cleaned_data["reagendada_para"]
                entrega.recebedor_nome = fechamento_form.cleaned_data["recebedor_nome"]
                entrega.recebedor_documento = fechamento_form.cleaned_data["recebedor_documento"]
                entrega.comprovante_observacao = fechamento_form.cleaned_data["comprovante_observacao"]
                campos = [
                    "status",
                    "motivo_insucesso",
                    "reagendada_para",
                    "recebedor_nome",
                    "recebedor_documento",
                    "comprovante_observacao",
                    "atualizado_em",
                ]
                if status == Entrega.Status.REAGENDADA:
                    entrega.data_prevista = entrega.reagendada_para
                    entrega.rota = None
                    campos.extend(["data_prevista", "rota"])
                entrega.save(update_fields=campos)
                _registrar_evento(entrega, EventoEntrega.Tipo.RETORNO, f"Retorno da rota registrado como {entrega.get_status_display()}.", request)
            messages.success(request, "Retorno registrado para as entregas selecionadas.")
        elif not entrega_ids:
            messages.error(request, "Selecione pelo menos uma entrega para registrar retorno.")
        else:
            messages.error(request, "Revise os dados de retorno.")

        rota.atualizar_finalizacao()

    return redirect(rota)


@login_required
def cadastros_operacionais(request):
    motorista_form = MotoristaForm(prefix="motorista")
    operador_form = OperadorForm(prefix="operador")
    motivo_form = MotivoInsucessoForm(prefix="motivo")

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        if tipo == "motorista":
            motorista_form = MotoristaForm(request.POST, prefix="motorista")
            if motorista_form.is_valid():
                motorista_form.save()
                messages.success(request, "Motorista cadastrado.")
                return redirect("entregas:cadastros")
        elif tipo == "operador":
            operador_form = OperadorForm(request.POST, prefix="operador")
            if operador_form.is_valid():
                operador_form.save()
                messages.success(request, "Operador cadastrado.")
                return redirect("entregas:cadastros")
        elif tipo == "motivo":
            motivo_form = MotivoInsucessoForm(request.POST, prefix="motivo")
            if motivo_form.is_valid():
                motivo_form.save()
                messages.success(request, "Motivo cadastrado.")
                return redirect("entregas:cadastros")

    return render(
        request,
        "entregas/cadastros.html",
        {
            "motorista_form": motorista_form,
            "operador_form": operador_form,
            "motivo_form": motivo_form,
            "motoristas": Motorista.objects.all(),
            "operadores": Operador.objects.all(),
            "motivos": MotivoInsucesso.objects.all(),
        },
    )
