from django import forms

from .models import Entrega, Motorista, MotivoInsucesso, Operador, Rota


class EntregaForm(forms.ModelForm):
    operador_cadastro = forms.ModelChoiceField(
        queryset=Operador.objects.filter(ativo=True),
        required=False,
        label="Operador(a) cadastrado",
        empty_label="Selecionar operador(a)",
    )
    motorista_cadastro = forms.ModelChoiceField(
        queryset=Motorista.objects.filter(ativo=True),
        required=False,
        label="Motorista cadastrado",
        empty_label="Selecionar motorista",
    )

    class Meta:
        model = Entrega
        fields = [
            "cliente",
            "rua",
            "numero",
            "bairro",
            "ponto_referencia",
            "volumes",
            "pdv",
            "data_prevista",
            "operador_cadastro",
            "operador",
            "motorista_cadastro",
            "motorista",
            "status",
            "observacoes",
        ]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "ponto_referencia": forms.TextInput(attrs={"placeholder": "Ex.: portão azul, ao lado da farmácia"}),
            "cliente": forms.TextInput(attrs={"autofocus": True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["operador"].required = False
        self.fields["motorista"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("operador_cadastro") and not cleaned_data.get("operador"):
            self.add_error("operador", "Informe ou selecione o operador.")
        if not cleaned_data.get("motorista_cadastro") and not cleaned_data.get("motorista"):
            self.add_error("motorista", "Informe ou selecione o motorista.")
        return cleaned_data

    def save(self, commit=True):
        entrega = super().save(commit=False)
        if entrega.operador_cadastro:
            entrega.operador = entrega.operador_cadastro.nome
        if entrega.motorista_cadastro:
            entrega.motorista = entrega.motorista_cadastro.nome
        if commit:
            entrega.save()
            self.save_m2m()
        return entrega


class RelatorioFiltroForm(forms.Form):
    data_inicio = forms.DateField(
        required=False,
        label="Data inicial",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    data_fim = forms.DateField(
        required=False,
        label="Data final",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    motorista = forms.CharField(required=False, label="Motorista", max_length=100)
    data_prevista = forms.DateField(
        required=False,
        label="Data prevista",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "Todos")] + list(Entrega.Status.choices),
    )


class RotaForm(forms.ModelForm):
    motorista_cadastro = forms.ModelChoiceField(
        queryset=Motorista.objects.filter(ativo=True),
        required=False,
        label="Motorista cadastrado",
        empty_label="Selecionar motorista",
    )

    class Meta:
        model = Rota
        fields = ["motorista_cadastro", "motorista", "responsavel_saida", "observacoes_saida"]
        widgets = {
            "motorista": forms.TextInput(attrs={"autofocus": True}),
            "observacoes_saida": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["motorista"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("motorista_cadastro") and not cleaned_data.get("motorista"):
            self.add_error("motorista", "Informe ou selecione o motorista.")
        return cleaned_data

    def save(self, commit=True):
        rota = super().save(commit=False)
        if rota.motorista_cadastro:
            rota.motorista = rota.motorista_cadastro.nome
        if commit:
            rota.save()
            self.save_m2m()
        return rota


class RetornoRotaForm(forms.Form):
    observacoes_retorno = forms.CharField(
        required=False,
        label="Observações do retorno",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class FechamentoEntregaForm(forms.Form):
    status = forms.ChoiceField(
        label="Resultado",
        choices=[
            (Entrega.Status.ENTREGUE, "Entregue"),
            (Entrega.Status.CANCELADA, "Cancelada"),
            (Entrega.Status.REAGENDADA, "Reagendada"),
        ],
    )
    motivo_insucesso = forms.ModelChoiceField(
        queryset=MotivoInsucesso.objects.filter(ativo=True),
        required=False,
        label="Motivo de insucesso",
        empty_label="Selecionar motivo",
    )
    reagendada_para = forms.DateField(
        required=False,
        label="Reagendada para",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    recebedor_nome = forms.CharField(required=False, label="Nome de quem recebeu", max_length=120)
    recebedor_documento = forms.CharField(required=False, label="Documento", max_length=40)
    comprovante_observacao = forms.CharField(
        required=False,
        label="Observação do comprovante",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        if status == Entrega.Status.ENTREGUE and not cleaned_data.get("recebedor_nome"):
            self.add_error("recebedor_nome", "Informe quem recebeu a entrega.")
        if status == Entrega.Status.CANCELADA and not cleaned_data.get("motivo_insucesso"):
            self.add_error("motivo_insucesso", "Informe o motivo do insucesso.")
        if status == Entrega.Status.REAGENDADA:
            if not cleaned_data.get("motivo_insucesso"):
                self.add_error("motivo_insucesso", "Informe o motivo do reagendamento.")
            if not cleaned_data.get("reagendada_para"):
                self.add_error("reagendada_para", "Informe a nova data.")
        return cleaned_data


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = ["nome", "telefone", "ativo"]


class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ["nome", "ativo"]


class MotivoInsucessoForm(forms.ModelForm):
    class Meta:
        model = MotivoInsucesso
        fields = ["descricao", "permite_reagendamento", "ativo"]
