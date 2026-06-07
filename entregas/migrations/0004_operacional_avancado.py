from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def criar_motivos_padrao(apps, schema_editor):
    MotivoInsucesso = apps.get_model("entregas", "MotivoInsucesso")
    motivos = [
        ("Cliente ausente", True),
        ("Endereço não localizado", True),
        ("Cliente recusou recebimento", False),
        ("Mercadoria avariada", True),
        ("Entrega reagendada pelo cliente", True),
    ]
    for descricao, permite_reagendamento in motivos:
        MotivoInsucesso.objects.get_or_create(
            descricao=descricao,
            defaults={"permite_reagendamento": permite_reagendamento, "ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("entregas", "0003_rotas"),
    ]

    operations = [
        migrations.CreateModel(
            name="Motorista",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100, unique=True, verbose_name="nome")),
                ("telefone", models.CharField(blank=True, max_length=30, verbose_name="telefone")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
            ],
            options={"verbose_name": "motorista", "verbose_name_plural": "motoristas", "ordering": ("nome",)},
        ),
        migrations.CreateModel(
            name="Operador",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100, unique=True, verbose_name="nome")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
            ],
            options={"verbose_name": "operador", "verbose_name_plural": "operadores", "ordering": ("nome",)},
        ),
        migrations.CreateModel(
            name="MotivoInsucesso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("descricao", models.CharField(max_length=100, unique=True, verbose_name="descrição")),
                ("permite_reagendamento", models.BooleanField(default=True, verbose_name="permite reagendamento")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativo")),
            ],
            options={"verbose_name": "motivo de insucesso", "verbose_name_plural": "motivos de insucesso", "ordering": ("descricao",)},
        ),
        migrations.AddField(
            model_name="entrega",
            name="comprovante_observacao",
            field=models.TextField(blank=True, verbose_name="observação do comprovante"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="data_prevista",
            field=models.DateField(default=django.utils.timezone.localdate, verbose_name="data prevista"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="recebedor_documento",
            field=models.CharField(blank=True, max_length=40, verbose_name="documento de quem recebeu"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="recebedor_nome",
            field=models.CharField(blank=True, max_length=120, verbose_name="nome de quem recebeu"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="reagendada_para",
            field=models.DateField(blank=True, null=True, verbose_name="reagendada para"),
        ),
        migrations.AlterField(
            model_name="entrega",
            name="status",
            field=models.CharField(
                choices=[
                    ("pendente", "Pendente"),
                    ("em_rota", "Em rota"),
                    ("entregue", "Entregue"),
                    ("cancelada", "Cancelada"),
                    ("reagendada", "Reagendada"),
                ],
                default="pendente",
                max_length=20,
                verbose_name="status",
            ),
        ),
        migrations.AddField(
            model_name="entrega",
            name="motivo_insucesso",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="entregas", to="entregas.motivoinsucesso", verbose_name="motivo de insucesso"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="motorista_cadastro",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="entregas", to="entregas.motorista", verbose_name="motorista cadastrado"),
        ),
        migrations.AddField(
            model_name="entrega",
            name="operador_cadastro",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="entregas", to="entregas.operador", verbose_name="operador cadastrado"),
        ),
        migrations.AddField(
            model_name="rota",
            name="motorista_cadastro",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="rotas", to="entregas.motorista", verbose_name="motorista cadastrado"),
        ),
        migrations.CreateModel(
            name="EventoEntrega",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("criada", "Criada"),
                            ("editada", "Editada"),
                            ("status", "Status alterado"),
                            ("rota", "Rota"),
                            ("retorno", "Retorno"),
                            ("reagendamento", "Reagendamento"),
                            ("comprovante", "Comprovante"),
                        ],
                        max_length=20,
                        verbose_name="tipo",
                    ),
                ),
                ("descricao", models.CharField(max_length=220, verbose_name="descrição")),
                ("usuario", models.CharField(blank=True, max_length=150, verbose_name="usuário")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("entrega", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="eventos", to="entregas.entrega")),
            ],
            options={"verbose_name": "evento da entrega", "verbose_name_plural": "eventos das entregas", "ordering": ("-criado_em",)},
        ),
        migrations.RunPython(criar_motivos_padrao, migrations.RunPython.noop),
    ]
