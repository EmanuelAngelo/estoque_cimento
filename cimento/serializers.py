from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

from .models import (
    EntradaEstoque,
    Estoque,
    ItemVenda,
    MovimentacaoEstoque,
    ProdutoCimento,
    TipoSaidaVenda,
    Venda,
)
from .services import EstoqueInsuficienteError, registrar_entrada, registrar_venda_simples


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class AuthLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if user is None:
            raise serializers.ValidationError('Usuário ou senha inválidos.')
        if not user.is_active:
            raise serializers.ValidationError('Usuário inativo.')
        attrs['user'] = user
        return attrs


class ProdutoCimentoSerializer(serializers.ModelSerializer):
    lucro_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    quantidade_estoque = serializers.SerializerMethodField()
    custo_medio_estoque = serializers.SerializerMethodField()

    def get_quantidade_estoque(self, obj: ProdutoCimento):
        estoque = getattr(obj, 'estoque', None)
        return int(getattr(estoque, 'quantidade_atual', 0) or 0)

    def get_custo_medio_estoque(self, obj: ProdutoCimento):
        estoque = getattr(obj, 'estoque', None)
        value = getattr(estoque, 'custo_medio_unitario', None)
        return value if value is not None else Decimal('0.00')

    class Meta:
        model = ProdutoCimento
        fields = [
            'id',
            'marca',
            'nome_produto',
            'descricao_produto',
            'peso_kg',
            'custo_unitario_fabrica',
            'custo_medio_estoque',
            'preco_unitario_loja',
            'lucro_unitario',
            'quantidade_estoque',
            'ativo',
            'created_at',
            'updated_at',
        ]


class EstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoCimentoSerializer(read_only=True)

    class Meta:
        model = Estoque
        fields = ['id', 'produto', 'quantidade_atual', 'custo_medio_unitario', 'updated_at']


class EntradaEstoqueCreateSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)
    custo_unitario_fabrica = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
    )
    data_entrada = serializers.DateField()
    fornecedor = serializers.CharField(required=False, allow_blank=True, default='')
    observacao = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_produto_id(self, value: int):
        if not ProdutoCimento.objects.filter(id=value, ativo=True).exists():
            raise serializers.ValidationError('Produto inválido ou inativo.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        produto = ProdutoCimento.objects.get(id=validated_data['produto_id'])
        return registrar_entrada(
            produto=produto,
            quantidade=validated_data['quantidade'],
            custo_unitario_fabrica=validated_data.get('custo_unitario_fabrica')
            if validated_data.get('custo_unitario_fabrica') is not None
            else produto.custo_unitario_fabrica,
            data_entrada=validated_data['data_entrada'],
            fornecedor=validated_data.get('fornecedor', ''),
            observacao=validated_data.get('observacao', ''),
            usuario=request.user,
        )


class EntradaEstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoCimentoSerializer(read_only=True)
    usuario_responsavel = serializers.CharField(source='usuario_responsavel.username', read_only=True)

    class Meta:
        model = EntradaEstoque
        fields = [
            'id',
            'produto',
            'quantidade',
            'custo_unitario_fabrica',
            'data_entrada',
            'fornecedor',
            'observacao',
            'cancelada',
            'usuario_responsavel',
        ]


class EntradaEstoqueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntradaEstoque
        fields = ['data_entrada', 'fornecedor', 'observacao']


class ItemVendaSerializer(serializers.ModelSerializer):
    produto = ProdutoCimentoSerializer(read_only=True)

    class Meta:
        model = ItemVenda
        fields = [
            'id',
            'produto',
            'quantidade',
            'peso_kg_unitario',
            'custo_unitario',
            'preco_unitario',
            'lucro_unitario',
            'subtotal_venda',
            'subtotal_custo',
            'subtotal_lucro',
        ]


class VendaSerializer(serializers.ModelSerializer):
    itens = ItemVendaSerializer(many=True, read_only=True)
    usuario_responsavel = serializers.CharField(source='usuario_responsavel.username', read_only=True)

    class Meta:
        model = Venda
        fields = [
            'id',
            'cliente_nome',
            'data_venda',
            'tipo_saida',
            'valor_total_venda',
            'custo_total_venda',
            'lucro_total_venda',
            'observacao',
            'cancelada',
            'usuario_responsavel',
            'itens',
        ]


class VendaCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    cliente_nome = serializers.CharField()
    produto_id = serializers.IntegerField(write_only=True)
    quantidade = serializers.IntegerField(min_value=1, write_only=True)
    data_venda = serializers.DateTimeField(required=False)
    tipo_saida = serializers.ChoiceField(choices=TipoSaidaVenda.choices)
    valor_total_venda = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    custo_total_venda = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    lucro_total_venda = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    valor_unitario_venda = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        write_only=True,
        min_value=Decimal('0'),
    )
    observacao = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_cliente_nome(self, value: str):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Nome do cliente é obrigatório.')
        return value

    def validate_produto_id(self, value: int):
        if not ProdutoCimento.objects.filter(id=value, ativo=True).exists():
            raise serializers.ValidationError('Produto inválido ou inativo.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        produto = ProdutoCimento.objects.get(id=validated_data['produto_id'])
        try:
            venda = registrar_venda_simples(
                cliente_nome=validated_data['cliente_nome'],
                produto=produto,
                quantidade=validated_data['quantidade'],
                data_venda=validated_data.get('data_venda') or timezone.now(),
                tipo_saida=validated_data['tipo_saida'],
                preco_unitario=validated_data.get('valor_unitario_venda'),
                observacao=validated_data.get('observacao', ''),
                usuario=request.user,
            )
        except EstoqueInsuficienteError as exc:
            raise serializers.ValidationError(
                {'quantidade': f'Estoque insuficiente. Disponível: {exc.quantidade_disponivel}'}
            )
        return venda


class VendaUpdateSerializer(serializers.Serializer):
    cliente_nome = serializers.CharField(required=False)
    data_venda = serializers.DateTimeField(required=False)
    tipo_saida = serializers.ChoiceField(choices=TipoSaidaVenda.choices, required=False)
    observacao = serializers.CharField(required=False, allow_blank=True)
    valor_unitario_venda = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
    )

    def validate_cliente_nome(self, value: str):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Nome do cliente é obrigatório.')
        return value


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoCimentoSerializer(read_only=True)
    usuario_responsavel = serializers.CharField(source='usuario_responsavel.username', read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'id',
            'produto',
            'tipo_movimentacao',
            'quantidade',
            'data_movimentacao',
            'referencia_tipo',
            'referencia_id',
            'observacao',
            'usuario_responsavel',
        ]
