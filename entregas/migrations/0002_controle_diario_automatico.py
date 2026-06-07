from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def preencher_controles_diarios(apps, schema_editor):
    Entrega = apps.get_model("entregas", "Entrega")
    sequencias_por_data = {}

    for entrega in Entrega.objects.order_by("criado_em", "id"):
        data_controle = entrega.criado_em.date() if entrega.criado_em else django.utils.timezone.localdate()
        proxima_sequencia = sequencias_por_data.get(data_controle, 0) + 1
        sequencias_por_data[data_controle] = proxima_sequencia

        entrega.data_controle = data_controle
        entrega.sequencia_controle = proxima_sequencia
        if not entrega.numero_controle:
            entrega.numero_controle = f"{data_controle:%Y%m%d}-{proxima_sequencia:03d}"
        entrega.save(update_fields=["data_controle", "sequencia_controle", "numero_controle"])


class Migration(migrations.Migration):
    dependencies = [
        ("entregas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="entrega",
            name="data_controle",
            field=models.DateField(
                default=django.utils.timezone.localdate,
                editable=False,
                verbose_name="data do controle",
            ),
        ),
        migrations.AddField(
            model_name="entrega",
            name="sequencia_controle",
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name="sequência do controle"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="entrega",
            name="numero_controle",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=30,
                unique=True,
                verbose_name="número de controle",
            ),
        ),
        migrations.RunPython(preencher_controles_diarios, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="entrega",
            constraint=models.UniqueConstraint(
                fields=("data_controle", "sequencia_controle"),
                name="entrega_controle_diario_unico",
            ),
        ),
    ]
