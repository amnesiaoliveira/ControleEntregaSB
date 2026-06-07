from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("entregas", "0002_controle_diario_automatico"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rota",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero_rota", models.CharField(blank=True, editable=False, max_length=30, unique=True, verbose_name="número da rota")),
                ("data_rota", models.DateField(default=django.utils.timezone.localdate, editable=False, verbose_name="data da rota")),
                ("sequencia_rota", models.PositiveIntegerField(editable=False, verbose_name="sequência da rota")),
                ("motorista", models.CharField(max_length=100, verbose_name="motorista")),
                ("responsavel_saida", models.CharField(blank=True, max_length=100, verbose_name="responsável pela saída")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("em_rota", "Em rota"),
                            ("finalizada", "Finalizada"),
                            ("cancelada", "Cancelada"),
                        ],
                        default="em_rota",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("observacoes_saida", models.TextField(blank=True, verbose_name="observações da saída")),
                ("observacoes_retorno", models.TextField(blank=True, verbose_name="observações do retorno")),
                ("criado_em", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("saida_em", models.DateTimeField(default=django.utils.timezone.now, verbose_name="saída em")),
                ("finalizada_em", models.DateTimeField(blank=True, null=True, verbose_name="finalizada em")),
            ],
            options={
                "verbose_name": "rota",
                "verbose_name_plural": "rotas",
                "ordering": ("-criado_em",),
            },
        ),
        migrations.AddField(
            model_name="entrega",
            name="rota",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="entregas",
                to="entregas.rota",
                verbose_name="rota",
            ),
        ),
        migrations.AddConstraint(
            model_name="rota",
            constraint=models.UniqueConstraint(
                fields=("data_rota", "sequencia_rota"),
                name="rota_controle_diario_unico",
            ),
        ),
    ]
