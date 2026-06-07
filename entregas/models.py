from django.db import models
from django.urls import reverse
from django.utils import timezone


class Motorista(models.Model):
    nome = models.CharField("nome", max_length=100, unique=True)
    telefone = models.CharField("telefone", max_length=30, blank=True)
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "motorista"
        verbose_name_plural = "motoristas"

    def __str__(self):
        return self.nome


class Operador(models.Model):
    nome = models.CharField("nome", max_length=100, unique=True)
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "operador"
        verbose_name_plural = "operadores"

    def __str__(self):
        return self.nome


class MotivoInsucesso(models.Model):
    descricao = models.CharField("descrição", max_length=100, unique=True)
    permite_reagendamento = models.BooleanField("permite reagendamento", default=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        ordering = ("descricao",)
        verbose_name = "motivo de insucesso"
        verbose_name_plural = "motivos de insucesso"

    def __str__(self):
        return self.descricao


class Rota(models.Model):
    class Status(models.TextChoices):
        EM_ROTA = "em_rota", "Em rota"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA = "cancelada", "Cancelada"

    numero_rota = models.CharField("número da rota", max_length=30, unique=True, blank=True, editable=False)
    data_rota = models.DateField("data da rota", default=timezone.localdate, editable=False)
    sequencia_rota = models.PositiveIntegerField("sequência da rota", editable=False)
    motorista = models.CharField("motorista", max_length=100)
    motorista_cadastro = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rotas",
        verbose_name="motorista cadastrado",
    )
    responsavel_saida = models.CharField("responsável pela saída", max_length=100, blank=True)
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.EM_ROTA)
    observacoes_saida = models.TextField("observações da saída", blank=True)
    observacoes_retorno = models.TextField("observações do retorno", blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    saida_em = models.DateTimeField("saída em", default=timezone.now)
    finalizada_em = models.DateTimeField("finalizada em", null=True, blank=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "rota"
        verbose_name_plural = "rotas"
        constraints = [
            models.UniqueConstraint(
                fields=["data_rota", "sequencia_rota"],
                name="rota_controle_diario_unico",
            )
        ]

    def __str__(self):
        return f"{self.numero_rota} - {self.motorista}"

    @classmethod
    def proxima_sequencia_do_dia(cls, data=None):
        data = data or timezone.localdate()
        ultima_sequencia = (
            cls.objects.filter(data_rota=data)
            .order_by("-sequencia_rota")
            .values_list("sequencia_rota", flat=True)
            .first()
        )
        return (ultima_sequencia or 0) + 1

    @classmethod
    def proximo_numero_rota(cls, data=None):
        data = data or timezone.localdate()
        return f"R{data:%Y%m%d}-{cls.proxima_sequencia_do_dia(data):03d}"

    def save(self, *args, **kwargs):
        if not self.numero_rota:
            self.data_rota = self.data_rota or timezone.localdate()
            self.sequencia_rota = self.proxima_sequencia_do_dia(self.data_rota)
            self.numero_rota = f"R{self.data_rota:%Y%m%d}-{self.sequencia_rota:03d}"
        super().save(*args, **kwargs)

    @property
    def total_volumes(self):
        return self.entregas.aggregate(total=models.Sum("volumes"))["total"] or 0

    @property
    def total_entregas(self):
        return self.entregas.count()

    def atualizar_finalizacao(self):
        abertas = self.entregas.exclude(
            status__in=[Entrega.Status.ENTREGUE, Entrega.Status.CANCELADA, Entrega.Status.REAGENDADA]
        ).exists()
        if not abertas and self.status != self.Status.FINALIZADA:
            self.status = self.Status.FINALIZADA
            self.finalizada_em = timezone.now()
            self.save(update_fields=["status", "finalizada_em"])

    def get_absolute_url(self):
        return reverse("entregas:rota_detalhe", kwargs={"pk": self.pk})


class Entrega(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_ROTA = "em_rota", "Em rota"
        ENTREGUE = "entregue", "Entregue"
        CANCELADA = "cancelada", "Cancelada"
        REAGENDADA = "reagendada", "Reagendada"

    numero_controle = models.CharField(
        "número de controle",
        max_length=30,
        unique=True,
        blank=True,
        editable=False,
    )
    data_controle = models.DateField("data do controle", default=timezone.localdate, editable=False)
    sequencia_controle = models.PositiveIntegerField("sequência do controle", editable=False)
    cliente = models.CharField("cliente", max_length=120)
    rua = models.CharField("rua", max_length=120)
    numero = models.CharField("número", max_length=20)
    bairro = models.CharField("bairro", max_length=80)
    ponto_referencia = models.CharField("ponto de referência", max_length=160, blank=True)
    volumes = models.PositiveIntegerField("quantidade de volumes")
    pdv = models.CharField("PDV", max_length=20)
    operador = models.CharField("operador(a)", max_length=100)
    operador_cadastro = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="entregas",
        verbose_name="operador cadastrado",
    )
    motorista = models.CharField("motorista", max_length=100)
    motorista_cadastro = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="entregas",
        verbose_name="motorista cadastrado",
    )
    rota = models.ForeignKey(
        Rota,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entregas",
        verbose_name="rota",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    data_prevista = models.DateField("data prevista", default=timezone.localdate)
    motivo_insucesso = models.ForeignKey(
        MotivoInsucesso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entregas",
        verbose_name="motivo de insucesso",
    )
    reagendada_para = models.DateField("reagendada para", null=True, blank=True)
    recebedor_nome = models.CharField("nome de quem recebeu", max_length=120, blank=True)
    recebedor_documento = models.CharField("documento de quem recebeu", max_length=40, blank=True)
    comprovante_observacao = models.TextField("observação do comprovante", blank=True)
    observacoes = models.TextField("observações", blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "entrega"
        verbose_name_plural = "entregas"
        constraints = [
            models.UniqueConstraint(
                fields=["data_controle", "sequencia_controle"],
                name="entrega_controle_diario_unico",
            )
        ]

    def __str__(self):
        return f"{self.numero_controle} - {self.cliente}"

    @classmethod
    def proxima_sequencia_do_dia(cls, data=None):
        data = data or timezone.localdate()
        ultima_sequencia = (
            cls.objects.filter(data_controle=data)
            .order_by("-sequencia_controle")
            .values_list("sequencia_controle", flat=True)
            .first()
        )
        return (ultima_sequencia or 0) + 1

    @classmethod
    def proximo_numero_controle(cls, data=None):
        data = data or timezone.localdate()
        return f"{data:%Y%m%d}-{cls.proxima_sequencia_do_dia(data):03d}"

    def save(self, *args, **kwargs):
        if not self.numero_controle:
            self.data_controle = self.data_controle or timezone.localdate()
            self.sequencia_controle = self.proxima_sequencia_do_dia(self.data_controle)
            self.numero_controle = f"{self.data_controle:%Y%m%d}-{self.sequencia_controle:03d}"
        super().save(*args, **kwargs)

    @property
    def endereco_completo(self):
        referencia = f" - Ref.: {self.ponto_referencia}" if self.ponto_referencia else ""
        return f"{self.rua}, {self.numero} - {self.bairro}{referencia}"

    def get_absolute_url(self):
        return reverse("entregas:detalhe", kwargs={"pk": self.pk})


class EventoEntrega(models.Model):
    class Tipo(models.TextChoices):
        CRIADA = "criada", "Criada"
        EDITADA = "editada", "Editada"
        STATUS = "status", "Status alterado"
        ROTA = "rota", "Rota"
        RETORNO = "retorno", "Retorno"
        REAGENDAMENTO = "reagendamento", "Reagendamento"
        COMPROVANTE = "comprovante", "Comprovante"

    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name="eventos")
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    descricao = models.CharField("descrição", max_length=220)
    usuario = models.CharField("usuário", max_length=150, blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "evento da entrega"
        verbose_name_plural = "eventos das entregas"

    def __str__(self):
        return f"{self.entrega.numero_controle} - {self.get_tipo_display()}"
