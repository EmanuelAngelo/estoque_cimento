from django.contrib import admin

from .models import (
	EntradaEstoque,
	Estoque,
	ItemOrcamento,
	ItemVenda,
	MovimentacaoEstoque,
	Orcamento,
	Produto,
	ProdutoConversaoUnidade,
	ProdutoPrecoVenda,
	Venda,
)


class ProdutoConversaoUnidadeInline(admin.TabularInline):
	model = ProdutoConversaoUnidade
	extra = 0


class ProdutoPrecoVendaInline(admin.TabularInline):
	model = ProdutoPrecoVenda
	extra = 0


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'tipo_material',
		'marca',
		'nome_produto',
		'unidade_estoque',
		'unidade_medida',
		'quantidade_por_unidade',
		'custo_unitario_fabrica',
		'preco_unitario_loja',
		'ativo',
	)
	list_filter = ('tipo_material', 'marca', 'ativo', 'unidade_estoque', 'unidade_medida')
	search_fields = ('nome_produto', 'descricao_produto')
	inlines = [ProdutoConversaoUnidadeInline, ProdutoPrecoVendaInline]


@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
	list_display = ('id', 'produto', 'quantidade_atual', 'updated_at')
	list_filter = ('produto__marca',)


@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'produto',
		'quantidade',
		'unidade_entrada',
		'quantidade_estoque',
		'custo_unitario_fabrica',
		'custo_total',
		'data_entrada',
		'usuario_responsavel',
	)
	list_filter = ('data_entrada', 'produto__marca')


class ItemVendaInline(admin.TabularInline):
	model = ItemVenda
	extra = 0


class ItemOrcamentoInline(admin.TabularInline):
	model = ItemOrcamento
	extra = 0


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'cliente_nome',
		'data_venda',
		'tipo_saida',
		'valor_total_venda',
		'lucro_total_venda',
		'usuario_responsavel',
	)
	list_filter = ('tipo_saida',)
	search_fields = ('cliente_nome',)
	inlines = [ItemVendaInline]


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
	list_display = ('id', 'cliente_nome', 'data_orcamento', 'valor_total', 'validade_dias', 'usuario_responsavel')
	search_fields = ('cliente_nome',)
	inlines = [ItemOrcamentoInline]


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'data_movimentacao',
		'produto',
		'tipo_movimentacao',
		'quantidade',
		'referencia_tipo',
		'referencia_id',
		'usuario_responsavel',
	)
	list_filter = ('tipo_movimentacao', 'produto__marca')
