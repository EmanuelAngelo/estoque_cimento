export function formatBRL(value: unknown): string {
  const n = Number(value ?? 0)
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function formatDateTime(value: unknown): string {
  if (!value) return ''
  const d = new Date(String(value))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString('pt-BR')
}

export function formatDate(value: unknown): string {
  if (!value) return ''
  const d = new Date(String(value))
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString('pt-BR')
}

export function formatMaterialLabel(produto: any): string {
  if (!produto) return ''
  const prefix = produto.marca_label || produto.marca || produto.tipo_material_label || produto.tipo_material || ''
  return prefix ? `${prefix} - ${produto.nome_produto}` : String(produto.nome_produto ?? '')
}

export function formatMaterialMeasure(produto: any): string {
  if (!produto) return ''
  const quantidade = Number(produto.quantidade_por_unidade ?? 0)
  const unidade = String(produto.unidade_medida_label || produto.unidade_medida || '').trim()
  if (!quantidade && !unidade) return ''
  if (!unidade) return formatQuantity(quantidade)
  return formatQuantityWithUnit(quantidade, produto.unidade_medida_label || produto.unidade_medida)
}

const unitLabelMap: Record<string, { singular: string; plural: string }> = {
  KG: { singular: 'Kg', plural: 'Kg' },
  UNIDADE: { singular: 'Unidade', plural: 'Unidades' },
  LATA: { singular: 'Lata', plural: 'Latas' },
  MILHEIRO: { singular: 'Milheiro', plural: 'Milheiros' },
  CARRADA: { singular: 'Carrada', plural: 'Carradas' },
  METRO: { singular: 'Metro', plural: 'Metros' },
  METRO_QUADRADO: { singular: 'Metro quadrado', plural: 'Metros quadrados' },
  METRO_CUBICO: { singular: 'Metro cúbico', plural: 'Metros cúbicos' },
  PACOTE: { singular: 'Pacote', plural: 'Pacotes' },
}

export function formatQuantity(value: unknown, maximumFractionDigits = 6): string {
  const n = Number(value ?? 0)
  if (!Number.isFinite(n)) return '0'
  return n.toLocaleString('pt-BR', {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  })
}

export function getUnitLabel(unit: unknown, quantity?: unknown): string {
  const entry = unitLabelMap[String(unit ?? '')]
  if (!entry) return String(unit ?? '')
  if (quantity == null) return entry.singular
  return Number(quantity) === 1 ? entry.singular : entry.plural
}

export function formatQuantityWithUnit(value: unknown, unit: unknown, maximumFractionDigits = 6): string {
  return `${formatQuantity(value, maximumFractionDigits)} ${getUnitLabel(unit, value)}`.trim()
}

export function convertProductQuantity(produto: any, quantidade: unknown, unidadeOrigem: unknown, unidadeDestino: unknown): number | null {
  const origem = String(unidadeOrigem ?? '')
  const destino = String(unidadeDestino ?? '')
  const quantity = Number(quantidade ?? 0)
  if (!produto || !origem || !destino || Number.isNaN(quantity)) return null
  if (origem === destino) return quantity

  const adjacency = new Map<string, Array<{ to: string; factor: number }>>()
  for (const conversao of produto.conversoes_unidade ?? []) {
    const from = String(conversao.unidade_origem)
    const to = String(conversao.unidade_destino)
    const factor = Number(conversao.fator_multiplicador)
    if (!from || !to || !factor) continue

    const forward = adjacency.get(from) ?? []
    forward.push({ to, factor })
    adjacency.set(from, forward)

    const backward = adjacency.get(to) ?? []
    backward.push({ to: from, factor: 1 / factor })
    adjacency.set(to, backward)
  }

  const queue: Array<{ unit: string; factor: number }> = [{ unit: origem, factor: 1 }]
  const visited = new Set<string>([origem])

  while (queue.length) {
    const current = queue.shift()!
    for (const edge of adjacency.get(current.unit) ?? []) {
      if (visited.has(edge.to)) continue
      const nextFactor = current.factor * edge.factor
      if (edge.to === destino) return quantity * nextFactor
      visited.add(edge.to)
      queue.push({ unit: edge.to, factor: nextFactor })
    }
  }

  return null
}

export function resolveProductSalePrice(produto: any, unidadeVenda: unknown): number {
  if (!produto) return 0

  const unidadeSelecionada = String(unidadeVenda || produto.unidade_medida || produto.unidade_estoque || '')
  const configuredPrice = (produto.precos_venda ?? []).find(
    (item: any) => item?.ativo !== false && String(item?.unidade_venda ?? '') === unidadeSelecionada,
  )
  if (configuredPrice?.preco_unitario != null) {
    return Number(configuredPrice.preco_unitario ?? 0)
  }

  const baseUnit = String(produto.unidade_medida || produto.unidade_estoque || unidadeSelecionada)
  const basePrice = Number(produto.preco_unitario_loja ?? 0)
  if (!unidadeSelecionada || unidadeSelecionada === baseUnit) return basePrice

  const factor = convertProductQuantity(produto, 1, unidadeSelecionada, baseUnit)
  if (factor == null) return basePrice
  return basePrice * factor
}

export function resolveProductUnitCost(produto: any, unidadeVenda: unknown): number {
  if (!produto) return 0

  const unidadeSelecionada = String(unidadeVenda || produto.unidade_estoque || '')
  const baseUnit = String(produto.unidade_estoque || unidadeSelecionada)
  const baseCost = Number(produto.custo_medio_estoque ?? 0) > 0
    ? Number(produto.custo_medio_estoque ?? 0)
    : Number(produto.custo_unitario_fabrica ?? 0)

  if (!unidadeSelecionada || unidadeSelecionada === baseUnit) return baseCost

  const factor = convertProductQuantity(produto, 1, unidadeSelecionada, baseUnit)
  if (factor == null) return baseCost
  return baseCost * factor
}
