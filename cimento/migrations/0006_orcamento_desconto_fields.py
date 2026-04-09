from django.db import migrations, models


def preencher_totais_orcamento(apps, schema_editor):
	Orcamento = apps.get_model('cimento', 'Orcamento')
	for orcamento in Orcamento.objects.all().iterator():
		orcamento.valor_total_bruto = orcamento.valor_total
		orcamento.desconto_percentual = 0
		orcamento.desconto_valor = 0
		orcamento.save(update_fields=['valor_total_bruto', 'desconto_percentual', 'desconto_valor'])


class Migration(migrations.Migration):

	dependencies = [
		('cimento', '0005_entradaestoque_custo_total_and_more'),
	]

	operations = [
		migrations.AddField(
			model_name='orcamento',
			name='desconto_percentual',
			field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
		),
		migrations.AddField(
			model_name='orcamento',
			name='desconto_valor',
			field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
		),
		migrations.AddField(
			model_name='orcamento',
			name='valor_total_bruto',
			field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
		),
		migrations.RunPython(preencher_totais_orcamento, migrations.RunPython.noop),
	]