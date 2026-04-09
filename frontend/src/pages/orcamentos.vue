<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Orçamentos" description="Monte propostas comerciais e gere PDF para o cliente">
      <template #actions>
        <AppButton icon="mdi-plus" @click="openDialog">Novo orçamento</AppButton>
        <AppButton variant="outline" icon="mdi-refresh" @click="load">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Orçamentos recentes</div>
          <div class="app-card-subtitle">Histórico de propostas geradas para clientes</div>
        </div>
      </div>

      <AppSpinner v-if="loading" />

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Cliente</th>
              <th class="text-right">Itens</th>
              <th class="text-right">Desconto</th>
              <th class="text-right">Total</th>
              <th>Validade</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="text-muted-foreground">{{ formatDateTime(item.data_orcamento) }}</td>
              <td class="font-medium">{{ item.cliente_nome }}</td>
              <td class="text-right text-muted-foreground">{{ item.itens?.length ?? 0 }}</td>
              <td class="text-right text-muted-foreground">{{ Number(item.desconto_percentual ?? 0).toFixed(2) }}%</td>
              <td class="text-right font-medium">{{ formatBRL(item.valor_total) }}</td>
              <td class="text-muted-foreground">{{ item.validade_dias }} dias</td>
              <td class="text-right">
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Baixar PDF"
                  @click="downloadPdf(item.id)"
                >
                  <span class="mdi mdi-file-pdf-box text-lg" />
                </button>
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Excluir"
                  @click="remove(item)"
                >
                  <span class="mdi mdi-trash-can-outline text-lg" />
                </button>
              </td>
            </tr>

            <tr v-if="!items.length">
              <td colspan="7">
                <EmptyState
                  icon="mdi-file-document-outline"
                  title="Sem orçamentos"
                  description="Clique em 'Novo orçamento' para montar a primeira proposta comercial."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal
      v-model="dialogOpen"
      title="Novo orçamento"
      description="Monte a proposta com os materiais, preços e validade"
      max-width="xl"
    >
      <form class="space-y-6" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-5">
            <AppInput v-model="form.cliente_nome" label="Cliente" placeholder="Nome do cliente" />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="form.validade_dias" label="Validade (dias)" type="number" min="1" step="1" />
          </div>
          <div class="md:col-span-4">
            <AppInput v-model="form.desconto_percentual" label="Desconto (%)" type="number" min="0" max="100" step="0.01" />
          </div>
          <div class="md:col-span-12">
            <AppTextarea v-model="form.observacao" label="Observação (opcional)" :rows="2" />
          </div>
        </div>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-semibold text-foreground">Itens do orçamento</div>
              <div class="text-sm text-muted-foreground">Defina quantidade e preço final praticado ao cliente.</div>
            </div>
            <AppButton variant="outline" icon="mdi-plus" @click="addRow">Adicionar item</AppButton>
          </div>

          <div v-for="(row, index) in form.itens" :key="index" class="rounded-(--radius) border border-border p-4">
            <div class="grid gap-4 md:grid-cols-12">
              <div class="md:col-span-4">
                <AppSelect
                  :model-value="row.produto_id"
                  :items="produtos"
                  item-title="label"
                  item-value="id"
                  label="Material"
                  placeholder="Selecione"
                  @update:modelValue="updateRowProduct(Number(index), $event)"
                />
              </div>
              <div class="md:col-span-2">
                <AppInput v-model="row.quantidade" :label="rowQuantityLabel(row)" type="number" min="0.001" step="0.001" />
              </div>
              <div class="md:col-span-2">
                <AppSelect
                  :model-value="row.unidade_venda"
                  :items="rowUnits(row)"
                  label="Unidade"
                  @update:modelValue="updateRowUnit(Number(index), $event)"
                />
              </div>
              <div class="md:col-span-2">
                <AppInput v-model="row.preco_unitario" label="Preço unit." type="number" min="0" step="0.01" />
              </div>
              <div class="md:col-span-1">
                <AppInput :model-value="rowMeasure(row)" label="Medida" readonly />
              </div>
              <div class="md:col-span-1 flex items-end justify-end">
                <AppButton variant="ghost" icon="mdi-delete-outline" @click="removeRow(Number(index))" :disabled="form.itens.length === 1" />
              </div>
            </div>
            <div class="mt-3 text-right text-sm text-muted-foreground">
              Subtotal: <span class="font-semibold text-foreground">{{ formatBRL(rowSubtotal(row)) }}</span>
            </div>
          </div>
        </div>

        <AppAlert variant="info">
          Total bruto: <strong>{{ formatBRL(totalBruto) }}</strong>.
          Desconto: <strong>{{ formatBRL(descontoValor) }}</strong>.
          Total final: <strong>{{ formatBRL(totalOrcamento) }}</strong>
        </AppAlert>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="closeDialog">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-file-check-outline" :loading="saving">Gerar orçamento</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/client'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { formatBRL, formatDateTime, formatMaterialLabel, formatMaterialMeasure, getUnitLabel } from '@/lib/formatters'

const items = ref<any[]>([])
const produtos = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogOpen = ref(false)

const form = ref<any>({})

const totalBruto = computed(() =>
  (form.value.itens ?? []).reduce((total: number, row: any) => total + rowSubtotal(row), 0),
)

const descontoValor = computed(() => totalBruto.value * (Number(form.value.desconto_percentual ?? 0) / 100))

const totalOrcamento = computed(() => totalBruto.value - descontoValor.value)

function resolvePrice(produto: any, unidadeVenda: string | null) {
  if (!produto) return 0
  const unidade = unidadeVenda || produto.unidade_estoque
  return Number(
    (produto.precos_venda ?? []).find((item: any) => item.ativo !== false && item.unidade_venda === unidade)?.preco_unitario ??
      produto.preco_unitario_loja ??
      0,
  )
}

function createRow() {
  const primeiroProduto = produtos.value[0] ?? null
  const unidadeVenda = primeiroProduto?.unidade_estoque ?? null
  return {
    produto_id: primeiroProduto?.id ?? null,
    unidade_venda: unidadeVenda,
    quantidade: 1,
    preco_unitario: resolvePrice(primeiroProduto, unidadeVenda),
  }
}

function reset() {
  form.value = {
    cliente_nome: '',
    validade_dias: 7,
    desconto_percentual: 0,
    observacao: '',
    itens: [createRow()],
  }
}

function getProduto(produtoId: unknown) {
  return produtos.value.find((produto) => produto.id === produtoId) ?? null
}

function rowMeasure(row: any) {
  return formatMaterialMeasure(getProduto(row.produto_id)) || '-'
}

function rowUnits(row: any) {
  const produto = getProduto(row.produto_id)
  if (!produto) return []
  const units = new Set<string>((produto.precos_venda ?? []).filter((item: any) => item.ativo !== false).map((item: any) => String(item.unidade_venda)))
  units.add(String(produto.unidade_estoque))
  return Array.from(units).map((unit) => ({ title: getUnitLabel(unit), value: unit }))
}

function rowQuantityLabel(row: any) {
  return row.unidade_venda ? `Qtd (${getUnitLabel(row.unidade_venda)})` : 'Qtd'
}

function rowSubtotal(row: any) {
  return Number(row.quantidade ?? 0) * Number(row.preco_unitario ?? 0)
}

function updateRowProduct(index: number, value: string | number | null) {
  const produtoId = value == null ? null : Number(value)
  const row = form.value.itens[index]
  row.produto_id = produtoId
  const produto = getProduto(produtoId)
  row.unidade_venda = produto?.unidade_estoque ?? null
  row.preco_unitario = resolvePrice(produto, row.unidade_venda)
}

function updateRowUnit(index: number, value: string | number | null) {
  const row = form.value.itens[index]
  row.unidade_venda = value == null ? null : String(value)
  row.preco_unitario = resolvePrice(getProduto(row.produto_id), row.unidade_venda)
}

function addRow() {
  form.value.itens.push(createRow())
}

function removeRow(index: number) {
  if (form.value.itens.length === 1) return
  form.value.itens.splice(index, 1)
}

function openDialog() {
  reset()
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  reset()
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function loadProdutos() {
  const { data } = await api.get('/produtos/?ativo=true&ordering=tipo_material,nome_produto')
  produtos.value = data.map((produto: any) => ({
    ...produto,
    label: formatMaterialLabel(produto),
  }))
}

async function loadOrcamentos(minDurationMs = 0) {
  const startedAt = Date.now()
  loading.value = true
  try {
    const { data } = await api.get('/orcamentos/?ordering=-data_orcamento')
    items.value = data
  } finally {
    const elapsed = Date.now() - startedAt
    if (elapsed < minDurationMs) await sleep(minDurationMs - elapsed)
    loading.value = false
  }
}

async function load() {
  await Promise.all([loadProdutos(), loadOrcamentos(0)])
}

async function save() {
  const payload = {
    cliente_nome: String(form.value.cliente_nome ?? '').trim(),
    validade_dias: Number(form.value.validade_dias ?? 7),
    desconto_percentual: String(form.value.desconto_percentual ?? 0),
    observacao: String(form.value.observacao ?? ''),
    itens: form.value.itens.map((row: any) => ({
      produto_id: Number(row.produto_id),
      quantidade: Number(row.quantidade ?? 0),
      unidade_venda: row.unidade_venda,
      preco_unitario: String(row.preco_unitario ?? 0),
    })),
  }

  saving.value = true
  try {
    await api.post('/orcamentos/', payload)
    await loadOrcamentos(0)
    closeDialog()
  } finally {
    saving.value = false
  }
}

async function downloadPdf(id: number) {
  const response = await api.get(`/orcamentos/${id}/pdf/`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `orcamento-${id}.pdf`
  link.click()
  window.URL.revokeObjectURL(url)
}

async function remove(item: any) {
  if (!confirm('Excluir este orçamento?')) return
  await api.delete(`/orcamentos/${item.id}/`)
  await loadOrcamentos(2000)
}

onMounted(async () => {
  await loadProdutos()
  reset()
  await loadOrcamentos(0)
})
</script>