from django.conf import settings
from django.db import models


class MarcaCimento(models.TextChoices):
	ITAQUI = 'ITAQUI', 'Itaqui'
	BRAVO = 'BRAVO', 'Bravo'
	POTY = 'POTY', 'Poty'
	MONTE_CARLOS = 'MONTE_CARLOS', 'Monte Carlos'


class TipoSaidaVenda(models.TextChoices):
	RETIRADA = 'RETIRADA', 'Retirada'
	ENTREGA = 'ENTREGA', 'Entrega'


class TipoMovimentacao(models.TextChoices):
	ENTRADA = 'ENTRADA', 'Entrada'
	SAIDA = 'SAIDA', 'Saída'


class ProdutoCimento(models.Model):
	marca = models.CharField(max_length=32, choices=MarcaCimento.choices)
	nome_produto = models.CharField(max_length=120)
	descricao_produto = models.TextField(blank=True, default='')
	peso_kg = models.DecimalField(max_digits=10, decimal_places=3)
	custo_unitario_fabrica = models.DecimalField(max_digits=12, decimal_places=2)
	preco_unitario_loja = models.DecimalField(max_digits=12, decimal_places=2)
	ativo = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['marca', 'nome_produto', 'id']

	def __str__(self) -> str:
		return f'{self.get_marca_display()} - {self.nome_produto}'

	@property
	def lucro_unitario(self):
		return self.preco_unitario_loja - self.custo_unitario_fabrica


class Estoque(models.Model):
	produto = models.OneToOneField(ProdutoCimento, on_delete=models.CASCADE, related_name='estoque')
	quantidade_atual = models.PositiveIntegerField(default=0)
	custo_medio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['produto__marca', 'produto__nome_produto', 'produto_id']

	def __str__(self) -> str:
		return f'Estoque({self.produto_id})={self.quantidade_atual}'


class EntradaEstoque(models.Model):
	produto = models.ForeignKey(ProdutoCimento, on_delete=models.PROTECT, related_name='entradas')
	quantidade = models.PositiveIntegerField()
	custo_unitario_fabrica = models.DecimalField(max_digits=12, decimal_places=2)
	data_entrada = models.DateField()
	fornecedor = models.CharField(max_length=120, blank=True, default='')
	observacao = models.TextField(blank=True, default='')
	cancelada = models.BooleanField(default=False)
	usuario_responsavel = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='entradas_estoque',
	)

	class Meta:
		ordering = ['-data_entrada', '-id']

	def __str__(self) -> str:
		return f'Entrada({self.produto_id}) x{self.quantidade} em {self.data_entrada}'


class Venda(models.Model):
	cliente_nome = models.CharField(max_length=120)
	data_venda = models.DateTimeField()
	tipo_saida = models.CharField(max_length=16, choices=TipoSaidaVenda.choices)

	valor_total_venda = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	custo_total_venda = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	lucro_total_venda = models.DecimalField(max_digits=14, decimal_places=2, default=0)

	observacao = models.TextField(blank=True, default='')
	cancelada = models.BooleanField(default=False)
	usuario_responsavel = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='vendas',
	)

	class Meta:
		ordering = ['-data_venda', '-id']

	def __str__(self) -> str:
		return f'Venda({self.id}) {self.cliente_nome}'


class ItemVenda(models.Model):
	venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
	produto = models.ForeignKey(ProdutoCimento, on_delete=models.PROTECT, related_name='itens_venda')
	quantidade = models.PositiveIntegerField()

	peso_kg_unitario = models.DecimalField(max_digits=10, decimal_places=3)
	custo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
	preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
	lucro_unitario = models.DecimalField(max_digits=12, decimal_places=2)

	subtotal_venda = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal_custo = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal_lucro = models.DecimalField(max_digits=14, decimal_places=2)

	class Meta:
		ordering = ['id']


class MovimentacaoEstoque(models.Model):
	produto = models.ForeignKey(ProdutoCimento, on_delete=models.PROTECT, related_name='movimentacoes')
	tipo_movimentacao = models.CharField(max_length=16, choices=TipoMovimentacao.choices)
	quantidade = models.PositiveIntegerField()
	data_movimentacao = models.DateTimeField(auto_now_add=True)

	referencia_tipo = models.CharField(max_length=32)
	referencia_id = models.PositiveIntegerField()
	observacao = models.TextField(blank=True, default='')
	usuario_responsavel = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='movimentacoes_estoque',
	)

	class Meta:
		ordering = ['-data_movimentacao', '-id']

