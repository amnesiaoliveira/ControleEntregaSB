from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Entrega",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_controle", models.CharField(max_length=30, unique=True, verbose_name="número de controle")),
                ("cliente", models.CharField(max_length=120, verbose_name="cliente")),
                ("rua", models.CharField(max_length=120, verbose_name="rua")),
                ("numero", models.CharField(max_length=20, verbose_name="número")),
                ("bairro", models.CharField(max_length=80, verbose_name="bairro")),
                ("ponto_referencia", models.CharField(blank=True, max_length=160, verbose_name="ponto de referência")),
                ("volumes", models.PositiveIntegerField(verbose_name="quantidade de volumes")),
                ("pdv", models.CharField(max_length=20, verbose_name="PDV")),
                ("operador", models.CharField(max_length=100, verbose_name="operador(a)")),
                ("motorista", models.CharField(max_length=100, verbose_name="motorista")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pendente", "Pendente"),
                            ("em_rota", "Em rota"),
                            ("entregue", "Entregue"),
                            ("cancelada", "Cancelada"),
                        ],
                        default="pendente",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("observacoes", models.TextField(blank=True, verbose_name="observações")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("atualizado_em", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
            ],
            options={
                "verbose_name": "entrega",
                "verbose_name_plural": "entregas",
                "ordering": ("-criado_em",),
            },
        ),
    ]
