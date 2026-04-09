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
  if (!unidade) return String(quantidade)
  return `${quantidade} ${unidade}`.trim()
}

const unitLabelMap: Record<string, string> = {
  KG: 'Kg',
  UNIDADE: 'Unidade',
  LATA: 'Lata',
  MILHEIRO: 'Milheiro',
  CARRADA: 'Carrada',
  METRO: 'Metro',
  METRO_QUADRADO: 'Metro quadrado',
  METRO_CUBICO: 'Metro cúbico',
  PACOTE: 'Pacote',
}

export function getUnitLabel(unit: unknown): string {
  return unitLabelMap[String(unit ?? '')] ?? String(unit ?? '')
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
