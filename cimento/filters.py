import django_filters

from .models import MovimentacaoEstoque, Venda


class VendaFilter(django_filters.FilterSet):
    data_inicial = django_filters.IsoDateTimeFilter(field_name='data_venda', lookup_expr='gte')
    data_final = django_filters.IsoDateTimeFilter(field_name='data_venda', lookup_expr='lte')
    cliente = django_filters.CharFilter(field_name='cliente_nome', lookup_expr='icontains')
    tipo_saida = django_filters.CharFilter(field_name='tipo_saida', lookup_expr='exact')
    marca = django_filters.CharFilter(field_name='itens__produto__marca', lookup_expr='exact')
    tipo_material = django_filters.CharFilter(field_name='itens__produto__tipo_material', lookup_expr='exact')

    class Meta:
        model = Venda
        fields = ['data_inicial', 'data_final', 'cliente', 'tipo_saida', 'marca', 'tipo_material']


class MovimentacaoFilter(django_filters.FilterSet):
    data_inicial = django_filters.IsoDateTimeFilter(field_name='data_movimentacao', lookup_expr='gte')
    data_final = django_filters.IsoDateTimeFilter(field_name='data_movimentacao', lookup_expr='lte')
    produto_id = django_filters.NumberFilter(field_name='produto_id', lookup_expr='exact')
    tipo = django_filters.CharFilter(field_name='tipo_movimentacao', lookup_expr='exact')

    class Meta:
        model = MovimentacaoEstoque
        fields = ['data_inicial', 'data_final', 'produto_id', 'tipo']
