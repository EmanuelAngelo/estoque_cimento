from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    EntradaEstoque,
    Estoque,
    ItemOrcamento,
    ItemVenda,
    MovimentacaoEstoque,
    Orcamento,
    Produto,
    TipoMovimentacao,
    TipoSaidaVenda,
    UnidadeMedida,
    Venda,
)

MONEY_PRECISION = Decimal('0.01')
QUANTITY_PRECISION = Decimal('0.000001')
STORE_NAME = 'Material de Construção'
STORE_PHONE = 'Telefone WhatsApp: 98 988495700'
STORE_ADDRESS_LINES = [
    'Endereço: Avenida Engenheiro Emiliano Macieira 22',
    'Km 03 BR 135 Tibiri',
    'São Luís, MA 65095600',
]
STORE_LOGO_PATH = Path(__file__).resolve().parent.parent / 'frontend' / 'public' / 'batatalogo.jpeg'


@dataclass(frozen=True)
class EstoqueInsuficienteError(Exception):
    produto_id: int
    quantidade_solicitada: Decimal
    quantidade_disponivel: Decimal

    def __str__(self) -> str:
        return (
            f'Estoque insuficiente para produto {self.produto_id}: '
            f'solicitado={self.quantidade_solicitada} disponivel={self.quantidade_disponivel}'
        )


@dataclass(frozen=True)
class ConversaoUnidadeNaoConfiguradaError(Exception):
    produto_id: int
    unidade_origem: str
    unidade_destino: str

    def __str__(self) -> str:
        return (
            f'Conversão não configurada para produto {self.produto_id}: '
            f'{self.unidade_origem} -> {self.unidade_destino}'
        )


@dataclass(frozen=True)
class PrecoVendaNaoConfiguradoError(Exception):
    produto_id: int
    unidade_venda: str

    def __str__(self) -> str:
        return f'Preço de venda não configurado para produto {self.produto_id} na unidade {self.unidade_venda}'


@dataclass(frozen=True)
class CalculoComercial:
    quantidade_venda: Decimal
    unidade_venda: str
    quantidade_estoque: Decimal
    fator_conversao_estoque: Decimal
    preco_unitario: Decimal
    custo_unitario: Decimal
    lucro_unitario: Decimal
    subtotal_venda: Decimal
    subtotal_custo: Decimal
    subtotal_lucro: Decimal


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value in {None, ''}:
        return Decimal('0')
    return Decimal(str(value))


def _quantize_money(value) -> Decimal:
    return _to_decimal(value).quantize(MONEY_PRECISION)


def _quantize_quantity(value) -> Decimal:
    return _to_decimal(value).quantize(QUANTITY_PRECISION)


def _require_positive_quantity(value, field_name: str = 'quantidade') -> Decimal:
    quantity = _quantize_quantity(value)
    if quantity <= 0:
        raise ValueError(f'{field_name} deve ser maior que zero.')
    return quantity


def _get_or_create_estoque_locked(produto: Produto) -> Estoque:
    estoque, _created = Estoque.objects.select_for_update().get_or_create(produto=produto)
    return estoque


def _resolve_custo_unitario_base(produto: Produto, estoque: Optional[Estoque] = None) -> Decimal:
    custo_medio = _to_decimal(getattr(estoque, 'custo_medio_unitario', 0) or 0)
    if custo_medio > 0:
        return _quantize_quantity(custo_medio)
    return _quantize_quantity(produto.custo_unitario_fabrica or 0)


def _iter_conversion_edges(produto: Produto):
    for conversao in produto.conversoes_unidade.filter(ativo=True).all():
        fator = _to_decimal(conversao.fator_multiplicador)
        if fator <= 0:
            continue
        yield conversao.unidade_origem, conversao.unidade_destino, fator
        yield conversao.unidade_destino, conversao.unidade_origem, Decimal('1') / fator


def resolver_fator_conversao(produto: Produto, unidade_origem: str, unidade_destino: str) -> Decimal:
    if unidade_origem == unidade_destino:
        return Decimal('1')

    fila = deque([(unidade_origem, Decimal('1'))])
    visitados = {unidade_origem}
    adjacencias: dict[str, list[tuple[str, Decimal]]] = {}
    for origem, destino, fator in _iter_conversion_edges(produto):
        adjacencias.setdefault(origem, []).append((destino, fator))

    while fila:
        unidade_atual, fator_atual = fila.popleft()
        for proxima_unidade, fator in adjacencias.get(unidade_atual, []):
            if proxima_unidade in visitados:
                continue

            fator_total = fator_atual * fator
            if proxima_unidade == unidade_destino:
                return _quantize_quantity(fator_total)

            visitados.add(proxima_unidade)
            fila.append((proxima_unidade, fator_total))

    raise ConversaoUnidadeNaoConfiguradaError(
        produto_id=produto.id,
        unidade_origem=unidade_origem,
        unidade_destino=unidade_destino,
    )


def converter_quantidade(produto: Produto, quantidade, unidade_origem: str, unidade_destino: str) -> Decimal:
    quantidade_decimal = _quantize_quantity(quantidade)
    fator = resolver_fator_conversao(produto, unidade_origem, unidade_destino)
    return _quantize_quantity(quantidade_decimal * fator)


def resolver_preco_venda(produto: Produto, unidade_venda: str, preco_unitario: Optional[Decimal] = None) -> Decimal:
    if preco_unitario is not None:
        return _quantize_money(preco_unitario)

    preco_configurado = (
        produto.precos_venda.filter(unidade_venda=unidade_venda, ativo=True).order_by('-updated_at', '-id').first()
    )
    if preco_configurado is not None:
        return _quantize_money(preco_configurado.preco_unitario)

    unidade_base_preco = produto.unidade_medida or produto.unidade_estoque
    if unidade_venda == unidade_base_preco:
        return _quantize_money(produto.preco_unitario_loja)

    try:
        quantidade_base = converter_quantidade(produto, Decimal('1'), unidade_venda, unidade_base_preco)
    except ConversaoUnidadeNaoConfiguradaError:
        quantidade_base = None

    if quantidade_base is not None and quantidade_base > 0:
        return _quantize_money(_to_decimal(produto.preco_unitario_loja) * quantidade_base)

    if unidade_venda == produto.unidade_estoque:
        return _quantize_money(produto.preco_unitario_loja)

    raise PrecoVendaNaoConfiguradoError(produto_id=produto.id, unidade_venda=unidade_venda)


def calcular_item_comercial(
    *,
    produto: Produto,
    quantidade,
    unidade_venda: str,
    custo_base_unitario: Decimal,
    preco_unitario: Optional[Decimal] = None,
) -> CalculoComercial:
    quantidade_venda = _require_positive_quantity(quantidade)
    quantidade_estoque = converter_quantidade(produto, quantidade_venda, unidade_venda, produto.unidade_estoque)
    fator_conversao = _quantize_quantity(quantidade_estoque / quantidade_venda)

    preco_unitario_final = resolver_preco_venda(produto, unidade_venda, preco_unitario)
    subtotal_venda = _quantize_money(preco_unitario_final * quantidade_venda)

    subtotal_custo_exato = _to_decimal(custo_base_unitario) * quantidade_estoque
    subtotal_custo = _quantize_money(subtotal_custo_exato)
    subtotal_lucro = _quantize_money(subtotal_venda - subtotal_custo)

    custo_unitario = _quantize_quantity(subtotal_custo_exato / quantidade_venda)
    lucro_unitario = _quantize_quantity(preco_unitario_final - custo_unitario)

    return CalculoComercial(
        quantidade_venda=quantidade_venda,
        unidade_venda=unidade_venda,
        quantidade_estoque=quantidade_estoque,
        fator_conversao_estoque=fator_conversao,
        preco_unitario=preco_unitario_final,
        custo_unitario=custo_unitario,
        lucro_unitario=lucro_unitario,
        subtotal_venda=subtotal_venda,
        subtotal_custo=subtotal_custo,
        subtotal_lucro=subtotal_lucro,
    )


@transaction.atomic
def registrar_entrada(
    *,
    produto: Produto,
    quantidade,
    custo_unitario_fabrica: Optional[Decimal],
    data_entrada,
    unidade_entrada: Optional[str] = None,
    custo_total: Optional[Decimal] = None,
    fornecedor: str = '',
    observacao: str = '',
    usuario,
) -> EntradaEstoque:
    quantidade_informada = _require_positive_quantity(quantidade)
    unidade_entrada_final = unidade_entrada or produto.unidade_estoque
    quantidade_estoque = converter_quantidade(
        produto,
        quantidade_informada,
        unidade_entrada_final,
        produto.unidade_estoque,
    )

    if custo_total is not None:
        custo_total_final = _quantize_money(custo_total)
        custo_unitario_informado = (
            _quantize_quantity(custo_total_final / quantidade_informada)
            if custo_unitario_fabrica is None
            else _quantize_quantity(custo_unitario_fabrica)
        )
    else:
        custo_unitario_informado = _quantize_quantity(
            custo_unitario_fabrica if custo_unitario_fabrica is not None else produto.custo_unitario_fabrica
        )
        custo_total_final = _quantize_money(custo_unitario_informado * quantidade_informada)

    custo_unitario_base = _quantize_quantity(custo_total_final / quantidade_estoque)

    entrada = EntradaEstoque.objects.create(
        produto=produto,
        quantidade=quantidade_informada,
        unidade_entrada=unidade_entrada_final,
        quantidade_estoque=quantidade_estoque,
        custo_unitario_fabrica=custo_unitario_informado,
        custo_total=custo_total_final,
        data_entrada=data_entrada,
        fornecedor=fornecedor or '',
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    estoque = _get_or_create_estoque_locked(produto)
    quantidade_anterior = _to_decimal(estoque.quantidade_atual)
    custo_medio_anterior = _to_decimal(estoque.custo_medio_unitario)

    nova_quantidade = quantidade_anterior + quantidade_estoque
    if nova_quantidade <= 0:
        novo_custo_medio = Decimal('0')
    elif quantidade_anterior <= 0 or custo_medio_anterior <= 0:
        novo_custo_medio = custo_unitario_base
    else:
        custo_total_anterior = quantidade_anterior * custo_medio_anterior
        custo_total_novo = quantidade_estoque * custo_unitario_base
        novo_custo_medio = _quantize_quantity((custo_total_anterior + custo_total_novo) / nova_quantidade)

    estoque.quantidade_atual = _quantize_quantity(nova_quantidade)
    estoque.custo_medio_unitario = novo_custo_medio
    estoque.save(update_fields=['quantidade_atual', 'custo_medio_unitario', 'updated_at'])

    produto.custo_unitario_fabrica = novo_custo_medio
    produto.save(update_fields=['custo_unitario_fabrica', 'updated_at'])

    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo_movimentacao=TipoMovimentacao.ENTRADA,
        quantidade=quantidade_estoque,
        referencia_tipo='ENTRADA_ESTOQUE',
        referencia_id=entrada.id,
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    return entrada


@transaction.atomic
def registrar_venda_simples(
    *,
    cliente_nome: str,
    produto: Produto,
    quantidade,
    data_venda: Optional[timezone.datetime] = None,
    tipo_saida: str,
    unidade_venda: Optional[str] = None,
    preco_unitario: Optional[Decimal] = None,
    observacao: str = '',
    usuario,
) -> Venda:
    if data_venda is None:
        data_venda = timezone.now()

    if tipo_saida not in {TipoSaidaVenda.RETIRADA, TipoSaidaVenda.ENTREGA}:
        raise ValueError('tipo_saida inválido')

    unidade_venda_final = unidade_venda or produto.unidade_estoque
    estoque = _get_or_create_estoque_locked(produto)
    custo_base_unitario = _resolve_custo_unitario_base(produto, estoque)
    calculo = calcular_item_comercial(
        produto=produto,
        quantidade=quantidade,
        unidade_venda=unidade_venda_final,
        custo_base_unitario=custo_base_unitario,
        preco_unitario=preco_unitario,
    )

    quantidade_disponivel = _to_decimal(estoque.quantidade_atual)
    if quantidade_disponivel < calculo.quantidade_estoque:
        raise EstoqueInsuficienteError(
            produto_id=produto.id,
            quantidade_solicitada=calculo.quantidade_estoque,
            quantidade_disponivel=quantidade_disponivel,
        )

    venda = Venda.objects.create(
        cliente_nome=cliente_nome,
        data_venda=data_venda,
        tipo_saida=tipo_saida,
        valor_total_venda=calculo.subtotal_venda,
        custo_total_venda=calculo.subtotal_custo,
        lucro_total_venda=calculo.subtotal_lucro,
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    ItemVenda.objects.create(
        venda=venda,
        produto=produto,
        quantidade=calculo.quantidade_venda,
        unidade_venda=calculo.unidade_venda,
        quantidade_estoque_baixada=calculo.quantidade_estoque,
        fator_conversao_estoque=calculo.fator_conversao_estoque,
        quantidade_por_unidade=produto.quantidade_por_unidade,
        custo_unitario=calculo.custo_unitario,
        preco_unitario=calculo.preco_unitario,
        lucro_unitario=calculo.lucro_unitario,
        subtotal_venda=calculo.subtotal_venda,
        subtotal_custo=calculo.subtotal_custo,
        subtotal_lucro=calculo.subtotal_lucro,
    )

    estoque.quantidade_atual = _quantize_quantity(quantidade_disponivel - calculo.quantidade_estoque)
    estoque.save(update_fields=['quantidade_atual', 'updated_at'])

    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo_movimentacao=TipoMovimentacao.SAIDA,
        quantidade=calculo.quantidade_estoque,
        referencia_tipo='VENDA',
        referencia_id=venda.id,
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    return venda


@transaction.atomic
def cancelar_entrada(*, entrada: EntradaEstoque, usuario) -> EntradaEstoque:
    if entrada.cancelada:
        return entrada

    estoque = _get_or_create_estoque_locked(entrada.produto)
    quantidade_movimentada = _to_decimal(entrada.quantidade_estoque)
    if _to_decimal(estoque.quantidade_atual) < quantidade_movimentada:
        raise ValueError('Não é possível cancelar: estoque atual menor que a quantidade da entrada.')

    estoque.quantidade_atual = _quantize_quantity(_to_decimal(estoque.quantidade_atual) - quantidade_movimentada)
    if estoque.quantidade_atual == 0:
        estoque.custo_medio_unitario = Decimal('0.000000')
    estoque.save(update_fields=['quantidade_atual', 'custo_medio_unitario', 'updated_at'])

    entrada.cancelada = True
    entrada.save(update_fields=['cancelada'])

    MovimentacaoEstoque.objects.create(
        produto=entrada.produto,
        tipo_movimentacao=TipoMovimentacao.SAIDA,
        quantidade=quantidade_movimentada,
        referencia_tipo='CANCELAMENTO_ENTRADA',
        referencia_id=entrada.id,
        observacao=entrada.observacao or '',
        usuario_responsavel=usuario,
    )
    return entrada


@transaction.atomic
def cancelar_venda(*, venda: Venda, usuario) -> Venda:
    if venda.cancelada:
        return venda

    itens = list(venda.itens.select_related('produto').all())
    if not itens:
        venda.cancelada = True
        venda.save(update_fields=['cancelada'])
        return venda

    for item in itens:
        estoque = _get_or_create_estoque_locked(item.produto)
        estoque.quantidade_atual = _quantize_quantity(
            _to_decimal(estoque.quantidade_atual) + _to_decimal(item.quantidade_estoque_baixada)
        )
        estoque.save(update_fields=['quantidade_atual', 'updated_at'])

        MovimentacaoEstoque.objects.create(
            produto=item.produto,
            tipo_movimentacao=TipoMovimentacao.ENTRADA,
            quantidade=item.quantidade_estoque_baixada,
            referencia_tipo='CANCELAMENTO_VENDA',
            referencia_id=venda.id,
            observacao=venda.observacao or '',
            usuario_responsavel=usuario,
        )

    venda.cancelada = True
    venda.save(update_fields=['cancelada'])
    return venda


@transaction.atomic
def atualizar_venda_metadata(
    *,
    venda: Venda,
    cliente_nome: Optional[str] = None,
    data_venda=None,
    tipo_saida: Optional[str] = None,
    observacao: Optional[str] = None,
    valor_unitario_venda: Optional[Decimal] = None,
) -> Venda:
    if venda.cancelada:
        raise ValueError('Venda cancelada não pode ser editada.')

    if cliente_nome is not None:
        venda.cliente_nome = (cliente_nome or '').strip()
    if data_venda is not None:
        venda.data_venda = data_venda
    if tipo_saida is not None:
        if tipo_saida not in {TipoSaidaVenda.RETIRADA, TipoSaidaVenda.ENTREGA}:
            raise ValueError('tipo_saida inválido')
        venda.tipo_saida = tipo_saida
    if observacao is not None:
        venda.observacao = observacao or ''

    item = venda.itens.select_related('produto').first()
    if item and valor_unitario_venda is not None:
        preco_unit = _quantize_money(valor_unitario_venda)
        subtotal_venda = _quantize_money(preco_unit * _to_decimal(item.quantidade))
        subtotal_custo = _quantize_money(_to_decimal(item.custo_unitario) * _to_decimal(item.quantidade))
        subtotal_lucro = _quantize_money(subtotal_venda - subtotal_custo)
        lucro_unit = _quantize_quantity(preco_unit - _to_decimal(item.custo_unitario))

        item.preco_unitario = preco_unit
        item.lucro_unitario = lucro_unit
        item.subtotal_venda = subtotal_venda
        item.subtotal_lucro = subtotal_lucro
        item.save(
            update_fields=[
                'preco_unitario',
                'lucro_unitario',
                'subtotal_venda',
                'subtotal_lucro',
            ]
        )

        venda.valor_total_venda = subtotal_venda
        venda.custo_total_venda = subtotal_custo
        venda.lucro_total_venda = subtotal_lucro

    venda.save()
    return venda


@transaction.atomic
def criar_orcamento(
    *,
    cliente_nome: str,
    itens: list[dict],
    usuario,
    validade_dias: int = 7,
    desconto_percentual: Decimal = Decimal('0'),
    observacao: str = '',
) -> Orcamento:
    orcamento = Orcamento.objects.create(
        cliente_nome=(cliente_nome or '').strip(),
        validade_dias=validade_dias,
        desconto_percentual=_quantize_money(desconto_percentual),
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    total_bruto = Decimal('0.00')
    for item in itens:
        produto = item.get('produto')
        if produto is not None:
            unidade_venda = item.get('unidade_venda') or produto.unidade_estoque
            calculo = calcular_item_comercial(
                produto=produto,
                quantidade=item['quantidade'],
                unidade_venda=unidade_venda,
                custo_base_unitario=_resolve_custo_unitario_base(produto),
                preco_unitario=item.get('preco_unitario'),
            )
            ItemOrcamento.objects.create(
                orcamento=orcamento,
                produto=produto,
                nome_produto='',
                quantidade=calculo.quantidade_venda,
                unidade_venda=calculo.unidade_venda,
                quantidade_estoque_referencia=calculo.quantidade_estoque,
                fator_conversao_estoque=calculo.fator_conversao_estoque,
                quantidade_por_unidade=produto.quantidade_por_unidade,
                preco_unitario=calculo.preco_unitario,
                subtotal=calculo.subtotal_venda,
            )
            total_bruto += calculo.subtotal_venda
        else:
            # custom item: product not registered. Use provided nome_produto, unidade_venda and preco_unitario
            nome = item.get('nome_produto', '')
            quantidade_venda = _require_positive_quantity(item['quantidade'])
            unidade_venda = item.get('unidade_venda') or UnidadeMedida.UNIDADE
            preco_unitario = _quantize_money(item.get('preco_unitario') or Decimal('0'))
            subtotal = _quantize_money(preco_unitario * quantidade_venda)
            ItemOrcamento.objects.create(
                orcamento=orcamento,
                produto=None,
                nome_produto=nome,
                quantidade=quantidade_venda,
                unidade_venda=unidade_venda,
                quantidade_estoque_referencia=quantidade_venda,
                fator_conversao_estoque=Decimal('1'),
                quantidade_por_unidade=Decimal('1'),
                preco_unitario=preco_unitario,
                subtotal=subtotal,
            )
            total_bruto += subtotal

    desconto_percentual_final = _to_decimal(desconto_percentual)
    desconto_valor = _quantize_money(total_bruto * desconto_percentual_final / Decimal('100'))
    total_liquido = _quantize_money(total_bruto - desconto_valor)
    orcamento.valor_total_bruto = _quantize_money(total_bruto)
    orcamento.desconto_percentual = desconto_percentual_final.quantize(Decimal('0.01'))
    orcamento.desconto_valor = desconto_valor
    orcamento.valor_total = total_liquido
    orcamento.save(update_fields=['valor_total_bruto', 'desconto_percentual', 'desconto_valor', 'valor_total'])
    return orcamento


def gerar_pdf_orcamento(orcamento: Orcamento, doc_type: str = 'orcamento') -> BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f'Orcamento {orcamento.id}',
    )

    styles = getSampleStyleSheet()
    palette = {
        'primary': colors.HexColor('#1f2937'),
        'accent': colors.HexColor('#c08b5c'),
        'text': colors.HexColor('#374151'),
        'muted': colors.HexColor('#6b7280'),
        'line': colors.HexColor('#e7e2da'),
        'line_soft': colors.HexColor('#f1ede7'),
        'surface': colors.HexColor('#fbf8f4'),
        'surface_alt': colors.HexColor('#f7f3ee'),
        'white': colors.white,
    }

    title_style = ParagraphStyle(
        'QuoteTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=palette['primary'],
        spaceAfter=2 * mm,
    )
    subtitle_style = ParagraphStyle(
        'QuoteSubtitle',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=palette['muted'],
    )
    store_name_style = ParagraphStyle(
        'StoreName',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=palette['primary'],
        spaceAfter=1 * mm,
    )
    store_info_style = ParagraphStyle(
        'StoreInfo',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=palette['text'],
    )
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=palette['muted'],
        textTransform=None,
    )
    meta_value_style = ParagraphStyle(
        'MetaValue',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=palette['primary'],
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=palette['primary'],
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=palette['text'],
    )
    table_cell_right_style = ParagraphStyle(
        'TableCellRight',
        parent=table_cell_style,
        alignment=TA_RIGHT,
    )
    summary_label_style = ParagraphStyle(
        'SummaryLabel',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12,
        textColor=palette['muted'],
    )
    summary_value_style = ParagraphStyle(
        'SummaryValue',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12,
        textColor=palette['primary'],
        alignment=TA_RIGHT,
    )
    total_label_style = ParagraphStyle(
        'TotalLabel',
        parent=summary_label_style,
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=palette['primary'],
    )
    total_value_style = ParagraphStyle(
        'TotalValue',
        parent=summary_value_style,
        fontSize=12,
        textColor=palette['accent'],
    )
    note_title_style = ParagraphStyle(
        'NoteTitle',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=palette['primary'],
    )
    note_body_style = ParagraphStyle(
        'NoteBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=palette['text'],
    )
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=palette['muted'],
        alignment=TA_RIGHT,
    )

    def paragraph(text, style):
        return Paragraph(str(text), style)

    def money_text(value: Decimal) -> str:
        # Format as Brazilian style: thousands separator '.' and decimal ','
        v = _quantize_money(value)
        s = f"{v:,.2f}"  # produces '1,250.00' in en_US style
        # swap separators: ',' -> temporary, '.' -> ',', temporary -> '.' => '1.250,00'
        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f'R$ {s}'

    def quantity_text(value: Decimal) -> str:
        return f'{_to_decimal(value):f}'.rstrip('0').rstrip('.') or '0'

    issued_at = timezone.localtime(orcamento.data_orcamento)
    validade = issued_at + timedelta(days=orcamento.validade_dias)

    story = []
    store_info_text = '<br/>'.join([STORE_PHONE, *STORE_ADDRESS_LINES])
    logo_flowable = ''
    if STORE_LOGO_PATH.exists():
        logo_flowable = Image(str(STORE_LOGO_PATH), width=26 * mm, height=26 * mm)

    # Title depends on document type: orcamento vs venda
    document_title = 'Orçamento de Materiais' if doc_type == 'orcamento' else 'Venda de Materiais'

    header_table = Table(
        [
            [
                logo_flowable,
                [
                    paragraph(STORE_NAME, store_name_style),
                    paragraph(document_title, title_style),
                    paragraph(
                        'Proposta comercial organizada para apresentação ao cliente.'
                        if doc_type == 'orcamento'
                        else 'Comprovante de venda para apresentação ao cliente.',
                        subtitle_style,
                    ),
                    Spacer(1, 1.5 * mm),
                    paragraph(store_info_text, store_info_style),
                ],
                paragraph(f'Orçamento #{orcamento.id}', table_cell_right_style),
            ]
        ],
        colWidths=[30 * mm, 102 * mm, 46 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), palette['surface']),
                ('BOX', (0, 0), (-1, -1), 0.6, palette['line']),
                ('LINEBELOW', (0, 0), (-1, -1), 0.6, palette['line']),
                ('LINEAFTER', (1, 0), (1, 0), 0.35, palette['line_soft']),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))

    info_table = Table(
        [
            [
                [paragraph('CLIENTE', meta_label_style), paragraph(orcamento.cliente_nome, meta_value_style)],
                [paragraph('EMISSÃO', meta_label_style), paragraph(issued_at.strftime('%d/%m/%Y %H:%M'), meta_value_style)],
            ],
            [
                [paragraph('VALIDADE', meta_label_style), paragraph(validade.strftime('%d/%m/%Y'), meta_value_style)],
                [paragraph('RESPONSÁVEL', meta_label_style), paragraph(orcamento.usuario_responsavel.username, meta_value_style)],
            ],
        ],
        colWidths=[89 * mm, 89 * mm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), palette['white']),
                ('BOX', (0, 0), (-1, -1), 0.5, palette['line']),
                ('INNERGRID', (0, 0), (-1, -1), 0.35, palette['line_soft']),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 7 * mm))

    itens_data = [
        [
            paragraph('Produto', table_header_style),
            paragraph('Qtd', table_header_style),
            paragraph('Unidade', table_header_style),
            paragraph('Preço unit.', table_header_style),
            paragraph('Subtotal', table_header_style),
        ]
    ]

    for item in orcamento.itens.select_related('produto').all():
        # Support items that reference a registered Produto or custom items (produto is None)
        if item.produto is not None:
            produto_nome = item.produto.nome_produto
            if item.produto.marca:
                produto_nome = f'{item.produto.get_marca_display()} - {produto_nome}'
        else:
            produto_nome = item.nome_produto or ''

        itens_data.append(
            [
                paragraph(produto_nome, table_cell_style),
                paragraph(quantity_text(item.quantidade), table_cell_right_style),
                paragraph(UnidadeMedida(item.unidade_venda).label, table_cell_style),
                paragraph(money_text(item.preco_unitario), table_cell_right_style),
                paragraph(money_text(item.subtotal), table_cell_right_style),
            ]
        )

    itens_table = Table(itens_data, colWidths=[84 * mm, 18 * mm, 28 * mm, 28 * mm, 30 * mm], repeatRows=1)
    itens_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), palette['surface_alt']),
        ('TEXTCOLOR', (0, 0), (-1, 0), palette['primary']),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, palette['line']),
        ('BOX', (0, 0), (-1, -1), 0.5, palette['line']),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, palette['line_soft']),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]
    for row_index in range(1, len(itens_data)):
        if row_index % 2 == 0:
            itens_style_commands.append(('BACKGROUND', (0, row_index), (-1, row_index), palette['surface']))
    itens_table.setStyle(TableStyle(itens_style_commands))
    story.append(itens_table)
    story.append(Spacer(1, 6 * mm))

    resumo_data = [
        [paragraph('Total bruto', summary_label_style), paragraph(money_text(orcamento.valor_total_bruto), summary_value_style)]
    ]
    if orcamento.desconto_percentual > 0:
        resumo_data.append(
            [
                paragraph(
                    f'Desconto ({orcamento.desconto_percentual:.2f}%)',
                    summary_label_style,
                ),
                paragraph(money_text(orcamento.desconto_valor), summary_value_style),
            ]
        )
    resumo_data.append([paragraph('Total final', total_label_style), paragraph(money_text(orcamento.valor_total), total_value_style)])

    resumo_table = Table(resumo_data, colWidths=[42 * mm, 38 * mm], hAlign='RIGHT')
    resumo_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), palette['surface']),
                ('BOX', (0, 0), (-1, -1), 0.6, palette['line']),
                ('INNERGRID', (0, 0), (-1, -1), 0.35, palette['line_soft']),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(resumo_table)

    if orcamento.observacao:
        story.append(Spacer(1, 7 * mm))
        observacao_table = Table(
            [[paragraph('Observações', note_title_style)], [paragraph(orcamento.observacao.replace('\n', '<br/>'), note_body_style)]],
            colWidths=[178 * mm],
        )
        observacao_table.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), palette['surface_alt']),
                    ('BACKGROUND', (0, 1), (-1, -1), palette['white']),
                    ('BOX', (0, 0), (-1, -1), 0.5, palette['line']),
                    ('LINEBELOW', (0, 0), (-1, 0), 0.35, palette['line']),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(observacao_table)

    story.append(Spacer(1, 8 * mm))
    story.append(paragraph('Obrigado pela preferência. Valores sujeitos à disponibilidade de estoque durante a validade deste orçamento.', footer_style))

    document.build(story)
    buffer.seek(0)
    return buffer
