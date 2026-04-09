from django.conf import settings
from django.db import migrations, models


def backfill_existing_products(apps, schema_editor):
    Produto = apps.get_model('cimento', 'Produto')
    Produto.objects.all().update(tipo_material='CIMENTO', unidade_medida='KG')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cimento', '0003_cancelamento_flags'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProdutoCimento',
            new_name='Produto',
        ),
        migrations.RenameField(
            model_name='itemvenda',
            old_name='peso_kg_unitario',
            new_name='quantidade_por_unidade',
        ),
        migrations.RenameField(
            model_name='produto',
            old_name='peso_kg',
            new_name='quantidade_por_unidade',
        ),
        migrations.AddField(
            model_name='produto',
            name='tipo_material',
            field=models.CharField(
                choices=[('CIMENTO', 'Cimento'), ('TIJOLO', 'Tijolo'), ('OUTRO', 'Outro')],
                default='OUTRO',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='produto',
            name='unidade_medida',
            field=models.CharField(
                choices=[
                    ('KG', 'Kg'),
                    ('UNIDADE', 'Unidade'),
                    ('METRO', 'Metro'),
                    ('METRO_QUADRADO', 'Metro quadrado'),
                    ('METRO_CUBICO', 'Metro cubico'),
                    ('PACOTE', 'Pacote'),
                ],
                default='UNIDADE',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='produto',
            name='marca',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ITAQUI', 'Itaqui'),
                    ('BRAVO', 'Bravo'),
                    ('POTY', 'Poty'),
                    ('MONTE_CARLOS', 'Monte Carlos'),
                ],
                default='',
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name='produto',
            name='quantidade_por_unidade',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=10),
        ),
        migrations.AlterModelOptions(
            name='produto',
            options={'ordering': ['tipo_material', 'marca', 'nome_produto', 'id']},
        ),
        migrations.RunPython(backfill_existing_products, migrations.RunPython.noop),
        migrations.CreateModel(
            name='Orcamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_nome', models.CharField(max_length=120)),
                ('data_orcamento', models.DateTimeField(auto_now_add=True)),
                ('validade_dias', models.PositiveIntegerField(default=7)),
                ('valor_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('observacao', models.TextField(blank=True, default='')),
                ('usuario_responsavel', models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='orcamentos', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-data_orcamento', '-id']},
        ),
        migrations.CreateModel(
            name='ItemOrcamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.PositiveIntegerField()),
                ('quantidade_por_unidade', models.DecimalField(decimal_places=3, max_digits=10)),
                ('preco_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=14)),
                ('orcamento', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='itens', to='cimento.orcamento')),
                ('produto', models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='itens_orcamento', to='cimento.produto')),
            ],
            options={'ordering': ['id']},
        ),
    ]