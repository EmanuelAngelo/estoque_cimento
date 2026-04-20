from django.conf import settings
from django.db import models


class MarcaCimento(models.TextChoices):
	ITAQUI = 'ITAQUI', 'Itaqui'
	APODI = 'APODI', 'Apodi'
	BRAVO = 'BRAVO', 'Bravo'
	POTY = 'POTY', 'Poty'
	MONTE_CARLOS = 'MONTE_CARLOS', 'Monte Carlos'


class TipoMaterial(models.TextChoices):
	CIMENTO = 'CIMENTO', 'Cimento'
	TIJOLO = 'TIJOLO', 'Tijolo'
	AREIA = 'AREIA', 'Areia'
	OUTRO = 'OUTRO', 'Outro'


class UnidadeMedida(models.TextChoices):
	KG = 'KG', 'Kg'
	UNIDADE = 'UNIDADE', 'Unidade'
	LATA = 'LATA', 'Lata'
	MILHEIRO = 'MILHEIRO', 'Milheiro'
	CARRADA = 'CARRADA', 'Carrada'
	METRO = 'METRO', 'Metro'
	METRO_QUADRADO = 'METRO_QUADRADO', 'Metro quadrado'
	METRO_CUBICO = 'METRO_CUBICO', 'Metro cubico'
	PACOTE = 'PACOTE', 'Pacote'


class TipoSaidaVenda(models.TextChoices):
	RETIRADA = 'RETIRADA', 'Retirada'
	ENTREGA = 'ENTREGA', 'Entrega'


class TipoMovimentacao(models.TextChoices):
	ENTRADA = 'ENTRADA', 'Entrada'
	SAIDA = 'SAIDA', 'Saída'


class Produto(models.Model):
	tipo_material = models.CharField(max_length=16, choices=TipoMaterial.choices, default=TipoMaterial.OUTRO)
	marca = models.CharField(max_length=32, choices=MarcaCimento.choices, blank=True, default='')
	nome_produto = models.CharField(max_length=120)
	descricao_produto = models.TextField(blank=True, default='')
	unidade_estoque = models.CharField(max_length=20, choices=UnidadeMedida.choices, default=UnidadeMedida.UNIDADE)
	unidade_medida = models.CharField(max_length=20, choices=UnidadeMedida.choices, default=UnidadeMedida.UNIDADE)
	quantidade_por_unidade = models.DecimalField(max_digits=10, decimal_places=3, default=1)
	custo_unitario_fabrica = models.DecimalField(max_digits=14, decimal_places=6)
	preco_unitario_loja = models.DecimalField(max_digits=12, decimal_places=2)
	ativo = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['tipo_material', 'marca', 'nome_produto', 'id']

	def __str__(self) -> str:
		prefixo = self.get_marca_display() if self.marca else self.get_tipo_material_display()
		return f'{prefixo} - {self.nome_produto}'

	@property
	def lucro_unitario(self):
		return self.preco_unitario_loja - self.custo_unitario_fabrica

	@property
	def exige_marca_cimento(self):
		return self.tipo_material == TipoMaterial.CIMENTO

	@property
	def unidade_estoque_display(self):
		return self.get_unidade_estoque_display()


class ProdutoConversaoUnidade(models.Model):
	produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='conversoes_unidade')
	unidade_origem = models.CharField(max_length=20, choices=UnidadeMedida.choices)
	unidade_destino = models.CharField(max_length=20, choices=UnidadeMedida.choices)
	fator_multiplicador = models.DecimalField(max_digits=14, decimal_places=6)
	ativo = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['unidade_origem', 'unidade_destino', 'id']
		constraints = [
			models.UniqueConstraint(
				fields=['produto', 'unidade_origem', 'unidade_destino'],
				name='cimento_conv_unidade_produto_unique',
			)
		]

	def __str__(self) -> str:
		return f'{self.produto_id}: 1 {self.unidade_origem} = {self.fator_multiplicador} {self.unidade_destino}'


class ProdutoPrecoVenda(models.Model):
	produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='precos_venda')
	unidade_venda = models.CharField(max_length=20, choices=UnidadeMedida.choices)
	preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
	ativo = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['unidade_venda', 'id']
		constraints = [
			models.UniqueConstraint(
				fields=['produto', 'unidade_venda'],
				name='cimento_preco_venda_produto_unique',
			)
		]

	def __str__(self) -> str:
		return f'{self.produto_id}: {self.unidade_venda} = {self.preco_unitario}'


class Estoque(models.Model):
	produto = models.OneToOneField(Produto, on_delete=models.CASCADE, related_name='estoque')
	quantidade_atual = models.DecimalField(max_digits=14, decimal_places=6, default=0)
	custo_medio_unitario = models.DecimalField(max_digits=14, decimal_places=6, default=0)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['produto__marca', 'produto__nome_produto', 'produto_id']

	def __str__(self) -> str:
		return f'Estoque({self.produto_id})={self.quantidade_atual}'


class EntradaEstoque(models.Model):
	produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='entradas')
	quantidade = models.DecimalField(max_digits=14, decimal_places=6)
	unidade_entrada = models.CharField(max_length=20, choices=UnidadeMedida.choices, default=UnidadeMedida.UNIDADE)
	quantidade_estoque = models.DecimalField(max_digits=14, decimal_places=6, default=0)
	custo_unitario_fabrica = models.DecimalField(max_digits=14, decimal_places=6)
	custo_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
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
	produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='itens_venda')
	quantidade = models.DecimalField(max_digits=14, decimal_places=6)
	unidade_venda = models.CharField(max_length=20, choices=UnidadeMedida.choices, default=UnidadeMedida.UNIDADE)
	quantidade_estoque_baixada = models.DecimalField(max_digits=14, decimal_places=6, default=0)
	fator_conversao_estoque = models.DecimalField(max_digits=14, decimal_places=6, default=1)

	quantidade_por_unidade = models.DecimalField(max_digits=10, decimal_places=3)
	custo_unitario = models.DecimalField(max_digits=14, decimal_places=6)
	preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
	lucro_unitario = models.DecimalField(max_digits=14, decimal_places=6)

	subtotal_venda = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal_custo = models.DecimalField(max_digits=14, decimal_places=2)
	subtotal_lucro = models.DecimalField(max_digits=14, decimal_places=2)

	class Meta:
		ordering = ['id']


class MovimentacaoEstoque(models.Model):
	produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='movimentacoes')
	tipo_movimentacao = models.CharField(max_length=16, choices=TipoMovimentacao.choices)
	quantidade = models.DecimalField(max_digits=14, decimal_places=6)
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


class Orcamento(models.Model):
	cliente_nome = models.CharField(max_length=120)
	data_orcamento = models.DateTimeField(auto_now_add=True)
	validade_dias = models.PositiveIntegerField(default=7)
	valor_total_bruto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	desconto_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
	desconto_valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	observacao = models.TextField(blank=True, default='')
	usuario_responsavel = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		related_name='orcamentos',
	)

	class Meta:
		ordering = ['-data_orcamento', '-id']

	def __str__(self) -> str:
		return f'Orcamento({self.id}) {self.cliente_nome}'


class ItemOrcamento(models.Model):
	orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens')
	produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_orcamento')
	# nome_produto allows storing a free-text product name when the item is not a registered Produto
	nome_produto = models.CharField(max_length=120, blank=True, default='')
	quantidade = models.DecimalField(max_digits=14, decimal_places=6)
	unidade_venda = models.CharField(max_length=20, choices=UnidadeMedida.choices, default=UnidadeMedida.UNIDADE)
	quantidade_estoque_referencia = models.DecimalField(max_digits=14, decimal_places=6, default=0)
	fator_conversao_estoque = models.DecimalField(max_digits=14, decimal_places=6, default=1)
	quantidade_por_unidade = models.DecimalField(max_digits=10, decimal_places=3)
	preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
	subtotal = models.DecimalField(max_digits=14, decimal_places=2)

	class Meta:
		ordering = ['id']

