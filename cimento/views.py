from __future__ import annotations

from django.http import FileResponse
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import MovimentacaoFilter, VendaFilter
from .models import EntradaEstoque, Estoque, ItemVenda, MovimentacaoEstoque, Orcamento, Produto, Venda
from .serializers import (
	AuthLoginSerializer,
	EntradaEstoqueCreateSerializer,
	EntradaEstoqueUpdateSerializer,
	EntradaEstoqueSerializer,
	EstoqueSerializer,
	MovimentacaoEstoqueSerializer,
	OrcamentoCreateSerializer,
	OrcamentoSerializer,
	ProdutoSerializer,
	UserMeSerializer,
	VendaCreateSerializer,
	VendaUpdateSerializer,
	VendaSerializer,
)

from .services import atualizar_venda_metadata, cancelar_entrada, cancelar_venda, gerar_pdf_orcamento


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


class HealthView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response({'status': 'ok'})


class DashboardView(APIView):
	def get(self, request):
		quantity_field = DecimalField(max_digits=20, decimal_places=6)
		quantity_zero = Value(0, output_field=quantity_field)
		total_qtd = Estoque.objects.aggregate(
			total=Coalesce(Sum('quantidade_atual'), quantity_zero, output_field=quantity_field)
		)['total']

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


class ProdutoViewSet(viewsets.ModelViewSet):
	queryset = Produto.objects.select_related('estoque').prefetch_related('conversoes_unidade', 'precos_venda').all()
	serializer_class = ProdutoSerializer
	filterset_fields = ['tipo_material', 'marca', 'ativo', 'unidade_medida']
	search_fields = ['nome_produto', 'descricao_produto']
	ordering_fields = ['tipo_material', 'marca', 'nome_produto', 'preco_unitario_loja', 'custo_unitario_fabrica', 'id']

	@staticmethod
	def _format_protected_references(exc: ProtectedError):
		labels = {
			'EntradaEstoque': 'entradas',
			'ItemVenda': 'vendas',
			'MovimentacaoEstoque': 'movimentações',
			'ItemOrcamento': 'orçamentos',
		}
		references = sorted({labels.get(obj.__class__.__name__, obj.__class__.__name__) for obj in exc.protected_objects})
		if not references:
			return 'histórico vinculado'
		if len(references) == 1:
			return references[0]
		if len(references) == 2:
			return f'{references[0]} e {references[1]}'
		return f"{', '.join(references[:-1])} e {references[-1]}"

	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		try:
			instance.delete()
		except ProtectedError as exc:
			references_text = self._format_protected_references(exc)
			if instance.ativo:
				instance.ativo = False
				instance.save(update_fields=['ativo', 'updated_at'])
				return Response(
					{
						'action': 'inactivated',
						'detail': (
							'Este material não pode ser excluído porque já possui '
							f'{references_text} vinculados. Para preservar o histórico, ele foi inativado.'
						),
					},
					status=status.HTTP_200_OK,
				)
			return Response(
				{
					'action': 'blocked',
					'detail': (
						'Este material não pode ser excluído porque já possui '
						f'{references_text} vinculados e já está inativo.'
					),
				},
				status=status.HTTP_200_OK,
			)

		return Response({'action': 'deleted', 'detail': 'Material excluído permanentemente.'}, status=status.HTTP_200_OK)


class EstoqueViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Estoque.objects.select_related('produto').prefetch_related('produto__conversoes_unidade', 'produto__precos_venda').all()
	serializer_class = EstoqueSerializer
	filterset_fields = ['produto__tipo_material', 'produto__marca', 'produto__ativo']
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

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		entrada = serializer.save()
		response_serializer = EntradaEstoqueSerializer(entrada)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class VendaViewSet(viewsets.ModelViewSet):
	queryset = (
		Venda.objects.select_related('usuario_responsavel')
		.prefetch_related('itens', 'itens__produto', 'itens__produto__conversoes_unidade', 'itens__produto__precos_venda')
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


class OrcamentoViewSet(viewsets.ModelViewSet):
	queryset = (
		Orcamento.objects.select_related('usuario_responsavel')
		.prefetch_related('itens', 'itens__produto', 'itens__produto__conversoes_unidade', 'itens__produto__precos_venda')
		.all()
	)
	http_method_names = ['get', 'post', 'patch', 'put', 'delete', 'head', 'options']
	ordering_fields = ['data_orcamento', 'valor_total', 'id']

	def get_serializer_class(self):
		if self.action == 'create':
			return OrcamentoCreateSerializer
		if self.action in {'update', 'partial_update'}:
			from .serializers import OrcamentoUpdateSerializer
			return OrcamentoUpdateSerializer
		return OrcamentoSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		orcamento = serializer.save()
		response_serializer = OrcamentoSerializer(orcamento)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED)

	def partial_update(self, request, pk=None):
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		orcamento = serializer.update(instance, serializer.validated_data)
		return Response(OrcamentoSerializer(orcamento).data)


class OrcamentoPdfView(APIView):
	def get(self, request, pk: int):
		orcamento = get_object_or_404(
			Orcamento.objects.select_related('usuario_responsavel').prefetch_related(
				'itens',
				'itens__produto',
				'itens__produto__conversoes_unidade',
				'itens__produto__precos_venda',
			),
			pk=pk,
		)
		# Support ?type=venda to render a sale-styled PDF instead of an orçamento
		doc_type = request.GET.get('type', 'orcamento')
		pdf_buffer = gerar_pdf_orcamento(orcamento, doc_type=doc_type)
		filename = f"{doc_type}-{orcamento.id}.pdf" if doc_type != 'orcamento' else f'orcamento-{orcamento.id}.pdf'
		return FileResponse(pdf_buffer, as_attachment=True, filename=filename)


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
		quantity_field = DecimalField(max_digits=20, decimal_places=6)
		quantity_zero = Value(0, output_field=quantity_field)
		money_field = DecimalField(max_digits=20, decimal_places=2)
		money_zero = Value(0, output_field=money_field)

		qs = (
			ItemVenda.objects.filter(venda_id__in=vendas_ids)
			.values('produto__marca')
			.annotate(
				quantidade_itens=Count('id'),
				quantidade_total=Coalesce(Sum('quantidade'), quantity_zero, output_field=quantity_field),
				total_vendido=Coalesce(Sum('subtotal_venda'), money_zero, output_field=money_field),
				total_lucro=Coalesce(Sum('subtotal_lucro'), money_zero, output_field=money_field),
			)
			.order_by('-total_vendido', 'produto__marca')
		)
		return Response(list(qs))
