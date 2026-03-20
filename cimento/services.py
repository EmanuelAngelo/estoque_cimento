from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    EntradaEstoque,
    Estoque,
    ItemVenda,
    MovimentacaoEstoque,
    ProdutoCimento,
    TipoMovimentacao,
    TipoSaidaVenda,
    Venda,
)


@dataclass(frozen=True)
class EstoqueInsuficienteError(Exception):
    produto_id: int
    quantidade_solicitada: int
    quantidade_disponivel: int

    def __str__(self) -> str:
        return (
            f'Estoque insuficiente para produto {self.produto_id}: '
            f'solicitado={self.quantidade_solicitada} disponivel={self.quantidade_disponivel}'
        )


def _get_or_create_estoque_locked(produto: ProdutoCimento) -> Estoque:
    estoque, _created = Estoque.objects.select_for_update().get_or_create(produto=produto)
    return estoque


@transaction.atomic
def registrar_entrada(
    *,
    produto: ProdutoCimento,
    quantidade: int,
    custo_unitario_fabrica: Decimal,
    data_entrada,
    fornecedor: str = '',
    observacao: str = '',
    usuario,
) -> EntradaEstoque:
    entrada = EntradaEstoque.objects.create(
        produto=produto,
        quantidade=quantidade,
        custo_unitario_fabrica=custo_unitario_fabrica,
        data_entrada=data_entrada,
        fornecedor=fornecedor or '',
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    estoque = _get_or_create_estoque_locked(produto)
    quantidade_int = int(quantidade)
    # Custo médio ponderado (método comum em sistemas de estoque)
    old_qty = int(estoque.quantidade_atual)
    old_avg = Decimal(estoque.custo_medio_unitario or 0)
    entrada_cost = Decimal(custo_unitario_fabrica).quantize(Decimal('0.01'))

    new_qty = old_qty + quantidade_int
    if new_qty <= 0:
        new_avg = Decimal('0.00')
    elif old_qty <= 0 or old_avg <= 0:
        new_avg = entrada_cost
    else:
        total_old = (old_avg * old_qty).quantize(Decimal('0.01'))
        total_new = (entrada_cost * quantidade_int).quantize(Decimal('0.01'))
        new_avg = ((total_old + total_new) / Decimal(new_qty)).quantize(Decimal('0.01'))

    estoque.quantidade_atual = new_qty
    estoque.custo_medio_unitario = new_avg
    estoque.save(update_fields=['quantidade_atual', 'custo_medio_unitario', 'updated_at'])



    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo_movimentacao=TipoMovimentacao.ENTRADA,
        quantidade=quantidade,
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
    produto: ProdutoCimento,
    quantidade: int,
    data_venda: Optional[timezone.datetime] = None,
    tipo_saida: str,
    preco_unitario: Optional[Decimal] = None,
    observacao: str = '',
    usuario,
) -> Venda:
    if data_venda is None:
        data_venda = timezone.now()

    if tipo_saida not in {TipoSaidaVenda.RETIRADA, TipoSaidaVenda.ENTREGA}:
        raise ValueError('tipo_saida inválido')

    preco_unitario_final = preco_unitario if preco_unitario is not None else produto.preco_unitario_loja
    quantidade_int = int(quantidade)

    estoque = _get_or_create_estoque_locked(produto)
    if estoque.quantidade_atual < quantidade_int:
        raise EstoqueInsuficienteError(
            produto_id=produto.id,
            quantidade_solicitada=quantidade_int,
            quantidade_disponivel=estoque.quantidade_atual,
        )

    custo_unitario_final = (
        Decimal(estoque.custo_medio_unitario or 0) if Decimal(estoque.custo_medio_unitario or 0) > 0 else produto.custo_unitario_fabrica
    ).quantize(Decimal('0.01'))
    lucro_unitario = (preco_unitario_final - custo_unitario_final).quantize(Decimal('0.01'))

    subtotal_venda = (preco_unitario_final * quantidade_int).quantize(Decimal('0.01'))
    subtotal_custo = (custo_unitario_final * quantidade_int).quantize(Decimal('0.01'))
    subtotal_lucro = (lucro_unitario * quantidade_int).quantize(Decimal('0.01'))

    venda = Venda.objects.create(
        cliente_nome=cliente_nome,
        data_venda=data_venda,
        tipo_saida=tipo_saida,
        valor_total_venda=subtotal_venda,
        custo_total_venda=subtotal_custo,
        lucro_total_venda=subtotal_lucro,
        observacao=observacao or '',
        usuario_responsavel=usuario,
    )

    ItemVenda.objects.create(
        venda=venda,
        produto=produto,
        quantidade=quantidade_int,
        peso_kg_unitario=produto.peso_kg,
        custo_unitario=custo_unitario_final,
        preco_unitario=preco_unitario_final,
        lucro_unitario=lucro_unitario,
        subtotal_venda=subtotal_venda,
        subtotal_custo=subtotal_custo,
        subtotal_lucro=subtotal_lucro,
    )

    estoque.quantidade_atual = estoque.quantidade_atual - quantidade_int
    estoque.save(update_fields=['quantidade_atual', 'updated_at'])

    MovimentacaoEstoque.objects.create(
        produto=produto,
        tipo_movimentacao=TipoMovimentacao.SAIDA,
        quantidade=quantidade_int,
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
    quantidade = int(entrada.quantidade)
    if estoque.quantidade_atual < quantidade:
        raise ValueError('Não é possível cancelar: estoque atual menor que a quantidade da entrada.')

    estoque.quantidade_atual = estoque.quantidade_atual - quantidade
    if estoque.quantidade_atual == 0:
        estoque.custo_medio_unitario = Decimal('0.00')
    estoque.save(update_fields=['quantidade_atual', 'custo_medio_unitario', 'updated_at'])

    entrada.cancelada = True
    entrada.save(update_fields=['cancelada'])

    MovimentacaoEstoque.objects.create(
        produto=entrada.produto,
        tipo_movimentacao=TipoMovimentacao.SAIDA,
        quantidade=quantidade,
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

    # Sistema atual é venda simples (1 item). Ainda assim, suporta N itens.
    for item in itens:
        estoque = _get_or_create_estoque_locked(item.produto)
        estoque.quantidade_atual = estoque.quantidade_atual + int(item.quantidade)
        estoque.save(update_fields=['quantidade_atual', 'updated_at'])

        MovimentacaoEstoque.objects.create(
            produto=item.produto,
            tipo_movimentacao=TipoMovimentacao.ENTRADA,
            quantidade=int(item.quantidade),
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
        preco_unit = Decimal(valor_unitario_venda).quantize(Decimal('0.01'))
        custo_unit = Decimal(item.custo_unitario).quantize(Decimal('0.01'))
        lucro_unit = (preco_unit - custo_unit).quantize(Decimal('0.01'))
        qtd = int(item.quantidade)

        item.preco_unitario = preco_unit
        item.lucro_unitario = lucro_unit
        item.subtotal_venda = (preco_unit * qtd).quantize(Decimal('0.01'))
        item.subtotal_lucro = (lucro_unit * qtd).quantize(Decimal('0.01'))
        item.save(
            update_fields=[
                'preco_unitario',
                'lucro_unitario',
                'subtotal_venda',
                'subtotal_lucro',
            ]
        )

        venda.valor_total_venda = item.subtotal_venda
        venda.custo_total_venda = (custo_unit * qtd).quantize(Decimal('0.01'))
        venda.lucro_total_venda = item.subtotal_lucro

    venda.save()
    return venda
