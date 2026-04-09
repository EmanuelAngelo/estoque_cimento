from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
	ItemOrcamento,
	Orcamento,
	Produto,
	ProdutoConversaoUnidade,
	ProdutoPrecoVenda,
	TipoMaterial,
	UnidadeMedida,
)


class BaseAuthenticatedAPITestCase(APITestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username='tester', password='senha123forte')
		self.client.force_authenticate(user=self.user)

	def create_areia(self):
		produto = Produto.objects.create(
			tipo_material=TipoMaterial.AREIA,
			nome_produto='Areia Lavada',
			descricao_produto='Areia para construção',
			unidade_estoque=UnidadeMedida.METRO,
			unidade_medida=UnidadeMedida.METRO,
			quantidade_por_unidade='1.000',
			custo_unitario_fabrica='58.333333',
			preco_unitario_loja='150.00',
			ativo=True,
		)
		ProdutoConversaoUnidade.objects.bulk_create(
			[
				ProdutoConversaoUnidade(
					produto=produto,
					unidade_origem=UnidadeMedida.CARRADA,
					unidade_destino=UnidadeMedida.METRO,
					fator_multiplicador='6.000000',
				),
				ProdutoConversaoUnidade(
					produto=produto,
					unidade_origem=UnidadeMedida.METRO,
					unidade_destino=UnidadeMedida.LATA,
					fator_multiplicador='50.000000',
				),
			]
		)
		ProdutoPrecoVenda.objects.bulk_create(
			[
				ProdutoPrecoVenda(produto=produto, unidade_venda=UnidadeMedida.CARRADA, preco_unitario='650.00'),
				ProdutoPrecoVenda(produto=produto, unidade_venda=UnidadeMedida.METRO, preco_unitario='150.00'),
				ProdutoPrecoVenda(produto=produto, unidade_venda=UnidadeMedida.LATA, preco_unitario='3.00'),
			]
		)
		return produto

	def create_tijolo(self):
		produto = Produto.objects.create(
			tipo_material=TipoMaterial.TIJOLO,
			nome_produto='Tijolo 8 Furos',
			descricao_produto='Tijolo cerâmico',
			unidade_estoque=UnidadeMedida.UNIDADE,
			unidade_medida=UnidadeMedida.UNIDADE,
			quantidade_por_unidade='1.000',
			custo_unitario_fabrica='0.700000',
			preco_unitario_loja='0.95',
			ativo=True,
		)
		ProdutoConversaoUnidade.objects.bulk_create(
			[
				ProdutoConversaoUnidade(
					produto=produto,
					unidade_origem=UnidadeMedida.CARRADA,
					unidade_destino=UnidadeMedida.UNIDADE,
					fator_multiplicador='10000.000000',
				),
				ProdutoConversaoUnidade(
					produto=produto,
					unidade_origem=UnidadeMedida.MILHEIRO,
					unidade_destino=UnidadeMedida.UNIDADE,
					fator_multiplicador='1000.000000',
				),
			]
		)
		ProdutoPrecoVenda.objects.bulk_create(
			[
				ProdutoPrecoVenda(produto=produto, unidade_venda=UnidadeMedida.MILHEIRO, preco_unitario='850.00'),
				ProdutoPrecoVenda(produto=produto, unidade_venda=UnidadeMedida.UNIDADE, preco_unitario='0.95'),
			]
		)
		return produto


class ProdutoApiTests(BaseAuthenticatedAPITestCase):
	def test_cria_material_nao_cimento_sem_marca(self):
		response = self.client.post(
			'/api/produtos/',
			{
				'tipo_material': TipoMaterial.TIJOLO,
				'marca': '',
				'nome_produto': 'Tijolo 8 furos',
				'descricao_produto': 'Unidade cerâmica',
				'unidade_estoque': UnidadeMedida.UNIDADE,
				'unidade_medida': UnidadeMedida.UNIDADE,
				'quantidade_por_unidade': '1.000',
				'custo_unitario_fabrica': '0.850000',
				'preco_unitario_loja': '1.30',
				'precos_venda': [
					{'unidade_venda': UnidadeMedida.UNIDADE, 'preco_unitario': '1.30', 'ativo': True}
				],
				'ativo': True,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		produto = Produto.objects.get(id=response.data['id'])
		self.assertEqual(produto.tipo_material, TipoMaterial.TIJOLO)
		self.assertEqual(produto.marca, '')
		self.assertEqual(produto.unidade_estoque, UnidadeMedida.UNIDADE)
		self.assertEqual(produto.precos_venda.count(), 1)

	def test_bloqueia_cimento_sem_marca(self):
		response = self.client.post(
			'/api/produtos/',
			{
				'tipo_material': TipoMaterial.CIMENTO,
				'marca': '',
				'nome_produto': 'CP-II 50kg',
				'descricao_produto': '',
				'unidade_estoque': UnidadeMedida.KG,
				'unidade_medida': UnidadeMedida.KG,
				'quantidade_por_unidade': '50.000',
				'custo_unitario_fabrica': '30.000000',
				'preco_unitario_loja': '39.90',
				'ativo': True,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('marca', response.data)


class AreiaVendaApiTests(BaseAuthenticatedAPITestCase):
	def setUp(self):
		super().setUp()
		self.areia = self.create_areia()

	def test_entrada_de_areia_por_carrada_vira_estoque_em_metros(self):
		response = self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.areia.id,
				'quantidade': '1.000000',
				'unidade_entrada': UnidadeMedida.CARRADA,
				'custo_unitario_fabrica': '350.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.areia.refresh_from_db()
		self.assertEqual(Decimal(response.data['quantidade_estoque']), Decimal('6.000000'))
		self.assertEqual(self.areia.estoque.quantidade_atual, Decimal('6.000000'))
		self.assertEqual(self.areia.estoque.custo_medio_unitario, Decimal('58.333333'))

	def test_venda_de_areia_por_carrada_calcula_custo_proporcional(self):
		self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.areia.id,
				'quantidade': '1.000000',
				'unidade_entrada': UnidadeMedida.CARRADA,
				'custo_unitario_fabrica': '350.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		response = self.client.post(
			'/api/vendas/',
			{
				'cliente_nome': 'Cliente Areia',
				'produto_id': self.areia.id,
				'quantidade': '1.000000',
				'unidade_venda': UnidadeMedida.CARRADA,
				'tipo_saida': 'RETIRADA',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Decimal(response.data['valor_total_venda']), Decimal('650.00'))
		self.assertEqual(Decimal(response.data['custo_total_venda']), Decimal('350.00'))
		self.assertEqual(Decimal(response.data['lucro_total_venda']), Decimal('300.00'))

	def test_venda_de_areia_por_metro_calcula_custo_proporcional(self):
		self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.areia.id,
				'quantidade': '1.000000',
				'unidade_entrada': UnidadeMedida.CARRADA,
				'custo_unitario_fabrica': '350.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		response = self.client.post(
			'/api/vendas/',
			{
				'cliente_nome': 'Cliente Metro',
				'produto_id': self.areia.id,
				'quantidade': '1.000000',
				'unidade_venda': UnidadeMedida.METRO,
				'tipo_saida': 'RETIRADA',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Decimal(response.data['valor_total_venda']), Decimal('150.00'))
		self.assertEqual(Decimal(response.data['custo_total_venda']), Decimal('58.33'))
		self.assertEqual(Decimal(response.data['lucro_total_venda']), Decimal('91.67'))


class TijoloVendaApiTests(BaseAuthenticatedAPITestCase):
	def setUp(self):
		super().setUp()
		self.tijolo = self.create_tijolo()

	def test_entrada_de_tijolo_por_milheiro_gera_dez_mil_unidades(self):
		response = self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.tijolo.id,
				'quantidade': '10.000000',
				'unidade_entrada': UnidadeMedida.MILHEIRO,
				'custo_unitario_fabrica': '700.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.tijolo.refresh_from_db()
		self.assertEqual(Decimal(response.data['quantidade_estoque']), Decimal('10000.000000'))
		self.assertEqual(self.tijolo.estoque.quantidade_atual, Decimal('10000.000000'))
		self.assertEqual(self.tijolo.estoque.custo_medio_unitario, Decimal('0.700000'))

	def test_venda_de_tijolo_por_milheiro(self):
		self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.tijolo.id,
				'quantidade': '10.000000',
				'unidade_entrada': UnidadeMedida.MILHEIRO,
				'custo_unitario_fabrica': '700.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		response = self.client.post(
			'/api/vendas/',
			{
				'cliente_nome': 'Cliente Tijolo',
				'produto_id': self.tijolo.id,
				'quantidade': '1.000000',
				'unidade_venda': UnidadeMedida.MILHEIRO,
				'tipo_saida': 'RETIRADA',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Decimal(response.data['valor_total_venda']), Decimal('850.00'))
		self.assertEqual(Decimal(response.data['custo_total_venda']), Decimal('700.00'))
		self.assertEqual(Decimal(response.data['lucro_total_venda']), Decimal('150.00'))

	def test_venda_de_tijolo_por_unidade(self):
		self.client.post(
			'/api/entradas/',
			{
				'produto_id': self.tijolo.id,
				'quantidade': '10.000000',
				'unidade_entrada': UnidadeMedida.MILHEIRO,
				'custo_unitario_fabrica': '700.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		response = self.client.post(
			'/api/vendas/',
			{
				'cliente_nome': 'Cliente Unitário',
				'produto_id': self.tijolo.id,
				'quantidade': '1.000000',
				'unidade_venda': UnidadeMedida.UNIDADE,
				'tipo_saida': 'RETIRADA',
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Decimal(response.data['valor_total_venda']), Decimal('0.95'))
		self.assertEqual(Decimal(response.data['custo_total_venda']), Decimal('0.70'))
		self.assertEqual(Decimal(response.data['lucro_total_venda']), Decimal('0.25'))


class OrcamentoApiTests(BaseAuthenticatedAPITestCase):
	def setUp(self):
		super().setUp()
		self.areia = self.create_areia()

	def test_cria_orcamento_com_unidade_de_venda(self):
		response = self.client.post(
			'/api/orcamentos/',
			{
				'cliente_nome': 'Cliente Teste',
				'validade_dias': 10,
				'desconto_percentual': '10.00',
				'observacao': 'Entrega a combinar.',
				'itens': [
					{
						'produto_id': self.areia.id,
						'quantidade': '2.000000',
						'unidade_venda': UnidadeMedida.METRO,
						'preco_unitario': '150.00',
					}
				],
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		orcamento = Orcamento.objects.get(id=response.data['id'])
		self.assertEqual(orcamento.cliente_nome, 'Cliente Teste')
		self.assertEqual(orcamento.validade_dias, 10)
		self.assertEqual(orcamento.valor_total_bruto, Decimal('300.00'))
		self.assertEqual(orcamento.desconto_percentual, Decimal('10.00'))
		self.assertEqual(orcamento.desconto_valor, Decimal('30.00'))
		self.assertEqual(orcamento.valor_total, Decimal('270.00'))
		self.assertEqual(orcamento.itens.count(), 1)
		self.assertEqual(ItemOrcamento.objects.get(orcamento=orcamento).unidade_venda, UnidadeMedida.METRO)

	def test_baixa_pdf_do_orcamento(self):
		orcamento = Orcamento.objects.create(
			cliente_nome='Cliente PDF',
			validade_dias=7,
			observacao='',
			usuario_responsavel=self.user,
			valor_total='39.90',
		)
		ItemOrcamento.objects.create(
			orcamento=orcamento,
			produto=self.areia,
			quantidade='1.000000',
			unidade_venda=UnidadeMedida.METRO,
			quantidade_estoque_referencia='1.000000',
			fator_conversao_estoque='1.000000',
			quantidade_por_unidade='1.000',
			preco_unitario='39.90',
			subtotal='39.90',
		)

		response = self.client.get(f'/api/orcamentos/{orcamento.id}/pdf/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response['Content-Type'], 'application/pdf')


class DashboardApiTests(BaseAuthenticatedAPITestCase):
	def test_dashboard_retorna_com_campos_decimais_sem_erro(self):
		areia = self.create_areia()
		self.client.post(
			'/api/entradas/',
			{
				'produto_id': areia.id,
				'quantidade': '1.000000',
				'unidade_entrada': UnidadeMedida.CARRADA,
				'custo_unitario_fabrica': '350.000000',
				'data_entrada': '2026-04-08',
			},
			format='json',
		)

		response = self.client.get('/api/dashboard/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(Decimal(str(response.data['quantidade_total_estoque'])), Decimal('6.000000'))
