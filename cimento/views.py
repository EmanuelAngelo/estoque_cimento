from __future__ import annotations

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import MovimentacaoFilter, VendaFilter
from .models import EntradaEstoque, Estoque, ItemVenda, MovimentacaoEstoque, ProdutoCimento, Venda
from .serializers import (
	AuthLoginSerializer,
	EntradaEstoqueCreateSerializer,
	EntradaEstoqueUpdateSerializer,
	EntradaEstoqueSerializer,
	EstoqueSerializer,
	MovimentacaoEstoqueSerializer,
	ProdutoCimentoSerializer,
	UserMeSerializer,
	VendaCreateSerializer,
	VendaUpdateSerializer,
	VendaSerializer,
)

from .services import atualizar_venda_metadata, cancelar_entrada, cancelar_venda


class AuthLoginView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = AuthLoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data['user']

		token, _created = Token.objects.get_or_create(user=user)
		return Response(
			{
				'token': token.key,
				'user': UserMeSerializer(user).data,
			}
		)


class AuthLogoutView(APIView):
	def post(self, request):
		Token.objects.filter(user=request.user).delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class AuthMeView(APIView):
	def get(self, request):
		return Response(UserMeSerializer(request.user).data)


class DashboardView(APIView):
	def get(self, request):
		total_qtd = Estoque.objects.aggregate(total=Coalesce(Sum('quantidade_atual'), 0))['total']

		money_field = DecimalField(max_digits=20, decimal_places=2)
		money_zero = Value(0, output_field=money_field)
		investido_expr = ExpressionWrapper(F('quantidade_atual') * F('custo_medio_unitario'), output_field=money_field)
		potencial_expr = ExpressionWrapper(
			F('quantidade_atual') * F('produto__preco_unitario_loja'),
			output_field=money_field,
		)

		agg = Estoque.objects.select_related('produto').aggregate(
			investido=Coalesce(Sum(investido_expr), money_zero, output_field=money_field),
			potencial=Coalesce(Sum(potencial_expr), money_zero, output_field=money_field),
		)
		investido = agg['investido']
		potencial = agg['potencial']
		lucro_potencial = potencial - investido

		now = timezone.localtime(timezone.now())
		inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0)
		inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		vendidos_dia = Venda.objects.filter(cancelada=False, data_venda__gte=inicio_dia).aggregate(
			total=Coalesce(Sum('valor_total_venda'), money_zero, output_field=money_field),
			lucro=Coalesce(Sum('lucro_total_venda'), money_zero, output_field=money_field),
		)
		vendidos_mes = Venda.objects.filter(cancelada=False, data_venda__gte=inicio_mes).aggregate(
			total=Coalesce(Sum('valor_total_venda'), money_zero, output_field=money_field),
			lucro=Coalesce(Sum('lucro_total_venda'), money_zero, output_field=money_field),
		)

		ultimas_vendas = (
			Venda.objects.filter(cancelada=False).prefetch_related('itens', 'itens__produto').all()[:5]
		)
		ultimas_vendas_data = VendaSerializer(ultimas_vendas, many=True).data

		estoque_baixo = (
			Estoque.objects.select_related('produto')
			.filter(produto__ativo=True, quantidade_atual__lte=10)
			.order_by('quantidade_atual')[:10]
		)
		estoque_baixo_data = EstoqueSerializer(estoque_baixo, many=True).data

		return Response(
			{
				'quantidade_total_estoque': total_qtd,
				'valor_total_investido_estoque': investido,
				'valor_total_potencial_venda': potencial,
				'lucro_potencial_estoque': lucro_potencial,
				'total_vendido_dia': vendidos_dia['total'],
				'total_vendido_mes': vendidos_mes['total'],
				'lucro_dia': vendidos_dia['lucro'],
				'lucro_mes': vendidos_mes['lucro'],
				'ultimas_vendas': ultimas_vendas_data,
				'produtos_estoque_baixo': estoque_baixo_data,
			}
		)


class ProdutoCimentoViewSet(viewsets.ModelViewSet):
	queryset = ProdutoCimento.objects.select_related('estoque').all()
	serializer_class = ProdutoCimentoSerializer
	filterset_fields = ['marca', 'ativo']
	search_fields = ['nome_produto', 'descricao_produto']
	ordering_fields = ['marca', 'nome_produto', 'preco_unitario_loja', 'custo_unitario_fabrica', 'id']


class EstoqueViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Estoque.objects.select_related('produto').all()
	serializer_class = EstoqueSerializer
	filterset_fields = ['produto__marca', 'produto__ativo']
	ordering_fields = ['quantidade_atual', 'updated_at', 'id']


class EntradaEstoqueViewSet(viewsets.ModelViewSet):
	queryset = EntradaEstoque.objects.select_related('produto', 'usuario_responsavel').filter(cancelada=False)
	http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
	ordering_fields = ['data_entrada', 'id']

	def get_serializer_class(self):
		if self.action == 'create':
			return EntradaEstoqueCreateSerializer
		if self.action in {'update', 'partial_update'}:
			return EntradaEstoqueUpdateSerializer
		return EntradaEstoqueSerializer

	def perform_destroy(self, instance):
		cancelar_entrada(entrada=instance, usuario=self.request.user)


class VendaViewSet(viewsets.ModelViewSet):
	queryset = (
		Venda.objects.select_related('usuario_responsavel')
		.prefetch_related('itens', 'itens__produto')
		.filter(cancelada=False)
	)
	http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
	filterset_class = VendaFilter
	ordering_fields = ['data_venda', 'valor_total_venda', 'lucro_total_venda', 'id']

	def get_serializer_class(self):
		if self.action == 'create':
			return VendaCreateSerializer
		if self.action in {'update', 'partial_update'}:
			return VendaUpdateSerializer
		return VendaSerializer

	def perform_destroy(self, instance):
		cancelar_venda(venda=instance, usuario=self.request.user)

	def partial_update(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = self.get_serializer(data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		atualizar_venda_metadata(
			venda=instance,
			cliente_nome=data.get('cliente_nome'),
			data_venda=data.get('data_venda'),
			tipo_saida=data.get('tipo_saida'),
			observacao=data.get('observacao'),
			valor_unitario_venda=data.get('valor_unitario_venda'),
		)
		return Response(VendaSerializer(instance).data)


class MovimentacaoEstoqueViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = MovimentacaoEstoque.objects.select_related('produto', 'usuario_responsavel').all()
	serializer_class = MovimentacaoEstoqueSerializer
	filterset_class = MovimentacaoFilter
	ordering_fields = ['data_movimentacao', 'id']


class RelatorioResumoView(APIView):
	"""Resumo de vendas/lucro por período."""

	def get(self, request):
		filtro = VendaFilter(request.GET, queryset=Venda.objects.filter(cancelada=False))
		qs = filtro.qs
		money_field = DecimalField(max_digits=20, decimal_places=2)
		money_zero = Value(0, output_field=money_field)
		resumo = qs.aggregate(
			total_vendido=Coalesce(Sum('valor_total_venda'), money_zero, output_field=money_field),
			total_custo=Coalesce(Sum('custo_total_venda'), money_zero, output_field=money_field),
			total_lucro=Coalesce(Sum('lucro_total_venda'), money_zero, output_field=money_field),
			quantidade_vendas=Coalesce(Count('id'), 0),
		)
		return Response(resumo)


class RelatorioPorClienteView(APIView):
	"""Agrupamento por cliente (com filtros de período e tipo/Marca via VendaFilter)."""

	def get(self, request):
		filtro = VendaFilter(request.GET, queryset=Venda.objects.filter(cancelada=False))
		money_field = DecimalField(max_digits=20, decimal_places=2)
		money_zero = Value(0, output_field=money_field)
		qs = (
			filtro.qs.values('cliente_nome')
			.annotate(
				quantidade_vendas=Count('id'),
				total_vendido=Coalesce(Sum('valor_total_venda'), money_zero, output_field=money_field),
				total_lucro=Coalesce(Sum('lucro_total_venda'), money_zero, output_field=money_field),
			)
			.order_by('-total_vendido', 'cliente_nome')
		)
		return Response(list(qs))


class RelatorioPorMarcaView(APIView):
	"""Agrupamento por marca (a partir dos itens de venda)."""

	def get(self, request):
		# Reaproveita os filtros de venda para recortar o período/cliente/tipo.
		filtro = VendaFilter(request.GET, queryset=Venda.objects.filter(cancelada=False))
		vendas_ids = filtro.qs.values_list('id', flat=True)
		money_field = DecimalField(max_digits=20, decimal_places=2)
		money_zero = Value(0, output_field=money_field)

		qs = (
			ItemVenda.objects.filter(venda_id__in=vendas_ids)
			.values('produto__marca')
			.annotate(
				quantidade_itens=Count('id'),
				quantidade_total=Coalesce(Sum('quantidade'), 0),
				total_vendido=Coalesce(Sum('subtotal_venda'), money_zero, output_field=money_field),
				total_lucro=Coalesce(Sum('subtotal_lucro'), money_zero, output_field=money_field),
			)
			.order_by('-total_vendido', 'produto__marca')
		)
		return Response(list(qs))
