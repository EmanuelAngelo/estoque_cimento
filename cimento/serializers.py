from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

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
    TipoMaterial,
    TipoSaidaVenda,
    UnidadeMedida,
    Venda,
)
from .services import (
    ConversaoUnidadeNaoConfiguradaError,
    EstoqueInsuficienteError,
    PrecoVendaNaoConfiguradoError,
    criar_orcamento,
    registrar_entrada,
    registrar_venda_simples,
)


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


class ProdutoConversaoUnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProdutoConversaoUnidade
        fields = ['id', 'unidade_origem', 'unidade_destino', 'fator_multiplicador', 'ativo']


class ProdutoPrecoVendaSerializer(serializers.ModelSerializer):
    unidade_venda_label = serializers.CharField(source='get_unidade_venda_display', read_only=True)

    class Meta:
        model = ProdutoPrecoVenda
        fields = ['id', 'unidade_venda', 'unidade_venda_label', 'preco_unitario', 'ativo']


class ProdutoSerializer(serializers.ModelSerializer):
    lucro_unitario = serializers.DecimalField(max_digits=14, decimal_places=6, read_only=True)
    quantidade_estoque = serializers.SerializerMethodField()
    custo_medio_estoque = serializers.SerializerMethodField()
    tipo_material_label = serializers.CharField(source='get_tipo_material_display', read_only=True)
    unidade_medida_label = serializers.CharField(source='get_unidade_medida_display', read_only=True)
    unidade_estoque_label = serializers.CharField(source='get_unidade_estoque_display', read_only=True)
    marca_label = serializers.SerializerMethodField()
    exige_marca_cimento = serializers.BooleanField(read_only=True)
    conversoes_unidade = ProdutoConversaoUnidadeSerializer(many=True, required=False)
    precos_venda = ProdutoPrecoVendaSerializer(many=True, required=False)

    def get_quantidade_estoque(self, obj: Produto):
        estoque = getattr(obj, 'estoque', None)
        return getattr(estoque, 'quantidade_atual', Decimal('0.000000')) or Decimal('0.000000')

    def get_custo_medio_estoque(self, obj: Produto):
        estoque = getattr(obj, 'estoque', None)
        value = getattr(estoque, 'custo_medio_unitario', None)
        return value if value is not None else Decimal('0.00')

    def get_marca_label(self, obj: Produto):
        return obj.get_marca_display() if obj.marca else ''

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tipo_material = attrs.get('tipo_material', getattr(self.instance, 'tipo_material', TipoMaterial.OUTRO))
        marca = attrs.get('marca', getattr(self.instance, 'marca', ''))

        if tipo_material == TipoMaterial.CIMENTO and not marca:
            raise serializers.ValidationError({'marca': 'Marca é obrigatória para cimento.'})

        if tipo_material != TipoMaterial.CIMENTO:
            attrs['marca'] = ''

        return attrs

    def _sync_relations(self, produto: Produto, conversoes_data, precos_data):
        if conversoes_data is not None:
            produto.conversoes_unidade.all().delete()
            ProdutoConversaoUnidade.objects.bulk_create(
                [ProdutoConversaoUnidade(produto=produto, **item) for item in conversoes_data]
            )
        if precos_data is not None:
            produto.precos_venda.all().delete()
            ProdutoPrecoVenda.objects.bulk_create([ProdutoPrecoVenda(produto=produto, **item) for item in precos_data])

    def create(self, validated_data):
        conversoes_data = validated_data.pop('conversoes_unidade', None)
        precos_data = validated_data.pop('precos_venda', None)
        produto = super().create(validated_data)
        self._sync_relations(produto, conversoes_data, precos_data)
        return produto

    def update(self, instance, validated_data):
        conversoes_data = validated_data.pop('conversoes_unidade', None)
        precos_data = validated_data.pop('precos_venda', None)
        produto = super().update(instance, validated_data)
        self._sync_relations(produto, conversoes_data, precos_data)
        return produto

    class Meta:
        model = Produto
        fields = [
            'id',
            'tipo_material',
            'tipo_material_label',
            'exige_marca_cimento',
            'marca',
            'marca_label',
            'nome_produto',
            'descricao_produto',
            'unidade_estoque',
            'unidade_estoque_label',
            'unidade_medida',
            'unidade_medida_label',
            'quantidade_por_unidade',
            'custo_unitario_fabrica',
            'custo_medio_estoque',
            'preco_unitario_loja',
            'lucro_unitario',
            'quantidade_estoque',
            'conversoes_unidade',
            'precos_venda',
            'ativo',
            'created_at',
            'updated_at',
        ]


class EstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)

    class Meta:
        model = Estoque
        fields = ['id', 'produto', 'quantidade_atual', 'custo_medio_unitario', 'updated_at']


class EntradaEstoqueCreateSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.DecimalField(max_digits=14, decimal_places=6, min_value=Decimal('0.000001'))
    unidade_entrada = serializers.ChoiceField(choices=UnidadeMedida.choices, required=False)
    custo_unitario_fabrica = serializers.DecimalField(
        max_digits=14,
        decimal_places=6,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
    )
    custo_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
    )
    data_entrada = serializers.DateField()
    fornecedor = serializers.CharField(required=False, allow_blank=True, default='')
    observacao = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_produto_id(self, value: int):
        if not Produto.objects.filter(id=value, ativo=True).exists():
            raise serializers.ValidationError('Produto inválido ou inativo.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        produto = Produto.objects.get(id=validated_data['produto_id'])
        return registrar_entrada(
            produto=produto,
            quantidade=validated_data['quantidade'],
            unidade_entrada=validated_data.get('unidade_entrada'),
            custo_unitario_fabrica=validated_data.get('custo_unitario_fabrica')
            if validated_data.get('custo_unitario_fabrica') is not None
            else produto.custo_unitario_fabrica,
            custo_total=validated_data.get('custo_total'),
            data_entrada=validated_data['data_entrada'],
            fornecedor=validated_data.get('fornecedor', ''),
            observacao=validated_data.get('observacao', ''),
            usuario=request.user,
        )


class EntradaEstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
    usuario_responsavel = serializers.CharField(source='usuario_responsavel.username', read_only=True)

    class Meta:
        model = EntradaEstoque
        fields = [
            'id',
            'produto',
            'quantidade',
            'unidade_entrada',
            'quantidade_estoque',
            'custo_unitario_fabrica',
            'custo_total',
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
    produto = ProdutoSerializer(read_only=True)

    class Meta:
        model = ItemVenda
        fields = [
            'id',
            'produto',
            'quantidade',
            'unidade_venda',
            'quantidade_estoque_baixada',
            'fator_conversao_estoque',
            'quantidade_por_unidade',
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
    quantidade = serializers.DecimalField(max_digits=14, decimal_places=6, min_value=Decimal('0.000001'), write_only=True)
    data_venda = serializers.DateTimeField(required=False)
    tipo_saida = serializers.ChoiceField(choices=TipoSaidaVenda.choices)
    unidade_venda = serializers.ChoiceField(choices=UnidadeMedida.choices, required=False)
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
        if not Produto.objects.filter(id=value, ativo=True).exists():
            raise serializers.ValidationError('Produto inválido ou inativo.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        produto = Produto.objects.get(id=validated_data['produto_id'])
        try:
            venda = registrar_venda_simples(
                cliente_nome=validated_data['cliente_nome'],
                produto=produto,
                quantidade=validated_data['quantidade'],
                data_venda=validated_data.get('data_venda') or timezone.now(),
                tipo_saida=validated_data['tipo_saida'],
                unidade_venda=validated_data.get('unidade_venda'),
                preco_unitario=validated_data.get('valor_unitario_venda'),
                observacao=validated_data.get('observacao', ''),
                usuario=request.user,
            )
        except EstoqueInsuficienteError as exc:
            raise serializers.ValidationError(
                {'quantidade': f'Estoque insuficiente. Disponível: {exc.quantidade_disponivel}'}
            )
        except (ConversaoUnidadeNaoConfiguradaError, PrecoVendaNaoConfiguradoError) as exc:
            raise serializers.ValidationError({'produto_id': str(exc)})
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


class ItemOrcamentoSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
    nome_produto = serializers.CharField(read_only=True)
    produto_label = serializers.SerializerMethodField()

    class Meta:
        model = ItemOrcamento
        fields = [
            'id',
            'produto',
            'produto_label',
            'nome_produto',
            'quantidade',
            'unidade_venda',
            'quantidade_estoque_referencia',
            'fator_conversao_estoque',
            'quantidade_por_unidade',
            'preco_unitario',
            'subtotal',
        ]

    def get_produto_label(self, obj: ItemOrcamento):
        if obj.produto is not None:
            return str(obj.produto)
        return obj.nome_produto or ''


class OrcamentoSerializer(serializers.ModelSerializer):
    itens = ItemOrcamentoSerializer(many=True, read_only=True)
    usuario_responsavel = serializers.CharField(source='usuario_responsavel.username', read_only=True)

    class Meta:
        model = Orcamento
        fields = [
            'id',
            'cliente_nome',
            'data_orcamento',
            'validade_dias',
            'valor_total_bruto',
            'desconto_percentual',
            'desconto_valor',
            'valor_total',
            'observacao',
            'usuario_responsavel',
            'itens',
        ]


class OrcamentoItemCreateSerializer(serializers.Serializer):
    # Either provide produto_id for a registered product OR nome_produto for a custom item
    produto_id = serializers.IntegerField(required=False)
    nome_produto = serializers.CharField(required=False, allow_blank=True, default='')
    quantidade = serializers.DecimalField(max_digits=14, decimal_places=6, min_value=Decimal('0.000001'))
    unidade_venda = serializers.ChoiceField(choices=UnidadeMedida.choices, required=False)
    preco_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
    )

    def validate_produto_id(self, value: int):
        if not Produto.objects.filter(id=value, ativo=True).exists():
            raise serializers.ValidationError('Produto inválido ou inativo.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        produto_id = attrs.get('produto_id')
        nome = attrs.get('nome_produto', '').strip()
        if not produto_id and not nome:
            raise serializers.ValidationError('Informe um produto cadastrado ou um nome de produto personalizado.')
        return attrs


class OrcamentoCreateSerializer(serializers.Serializer):
    cliente_nome = serializers.CharField()
    validade_dias = serializers.IntegerField(required=False, min_value=1, max_value=60, default=7)
    desconto_percentual = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        default=Decimal('0'),
    )
    observacao = serializers.CharField(required=False, allow_blank=True, default='')
    itens = OrcamentoItemCreateSerializer(many=True)

    def validate_cliente_nome(self, value: str):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Nome do cliente é obrigatório.')
        return value

    def validate_itens(self, value):
        if not value:
            raise serializers.ValidationError('Informe ao menos um item para o orçamento.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        itens = []
        for item in validated_data['itens']:
            if item.get('produto_id'):
                produto = Produto.objects.get(id=item['produto_id'])
                itens.append(
                    {
                        'produto': produto,
                        'quantidade': item['quantidade'],
                        'unidade_venda': item.get('unidade_venda'),
                        'preco_unitario': item.get('preco_unitario'),
                    }
                )
            else:
                # custom item (not a registered Produto)
                itens.append(
                    {
                        'produto': None,
                        'nome_produto': item.get('nome_produto', '').strip(),
                        'quantidade': item['quantidade'],
                        'unidade_venda': item.get('unidade_venda'),
                        'preco_unitario': item.get('preco_unitario') or Decimal('0'),
                    }
                )

        return criar_orcamento(
            cliente_nome=validated_data['cliente_nome'],
            itens=itens,
            validade_dias=validated_data.get('validade_dias', 7),
            desconto_percentual=validated_data.get('desconto_percentual', Decimal('0')),
            observacao=validated_data.get('observacao', ''),
            usuario=request.user,
        )


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto = ProdutoSerializer(read_only=True)
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
