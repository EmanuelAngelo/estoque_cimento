from django.contrib import admin

from .models import (
	EntradaEstoque,
	Estoque,
	ItemVenda,
	MovimentacaoEstoque,
	ProdutoCimento,
	Venda,
)


@admin.register(ProdutoCimento)
class ProdutoCimentoAdmin(admin.ModelAdmin):
	list_display = ('id', 'marca', 'nome_produto', 'peso_kg', 'custo_unitario_fabrica', 'preco_unitario_loja', 'ativo')
	list_filter = ('marca', 'ativo')
	search_fields = ('nome_produto', 'descricao_produto')


@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
	list_display = ('id', 'produto', 'quantidade_atual', 'updated_at')
	list_filter = ('produto__marca',)


@admin.register(EntradaEstoque)
class EntradaEstoqueAdmin(admin.ModelAdmin):
	list_display = ('id', 'produto', 'quantidade', 'custo_unitario_fabrica', 'data_entrada', 'usuario_responsavel')
	list_filter = ('data_entrada', 'produto__marca')


class ItemVendaInline(admin.TabularInline):
	model = ItemVenda
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
