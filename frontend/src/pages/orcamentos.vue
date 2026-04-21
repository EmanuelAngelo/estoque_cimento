<template>
  <div class="max-w-7xl mx-auto">
    <div
      v-if="downloadingPdfId !== null"
      class="fixed right-4 top-4 z-[80] flex items-center gap-3 rounded-[var(--radius)] border border-border bg-card px-4 py-3 shadow-lg"
      role="status"
      aria-live="polite"
    >
      <span class="h-4 w-4 animate-spin rounded-full border-2 border-primary/25 border-t-primary" />
      <div>
        <div class="text-sm font-semibold text-foreground">Gerando PDF do orçamento</div>
        <div class="text-xs text-muted-foreground">Aguarde, isso pode levar alguns segundos...</div>
      </div>
    </div>

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
                  :title="downloadingPdfId === item.id ? 'Gerando PDF...' : 'Baixar PDF'"
                  :disabled="downloadingPdfId === item.id"
                  @click="downloadPdf(item.id)"
                >
                  <span
                    v-if="downloadingPdfId === item.id"
                    class="inline-block h-[18px] w-[18px] animate-spin rounded-full border-2 border-current/25 border-t-current"
                  />
                  <span v-else class="mdi mdi-file-pdf-box text-lg" />
                </button>
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Editar"
                  @click="openEdit(item)"
                >
                  <span class="mdi mdi-pencil text-lg" />
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
      <form class="space-y-6" @submit.prevent="openActionDialog">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-5">
            <AppInput v-model="form.cliente_nome" label="Cliente" placeholder="Nome do cliente" />
          </div>
          <div class="md:col-span-2">
            <AppInput v-model="form.validade_dias" label="Validade (dias)" type="number" min="1" step="1" />
          </div>
          <div class="md:col-span-2">
            <AppInput v-model="descontoValorInput" label="Desconto (R$)" type="number" min="0" step="0.01" />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="descontoPercentual" label="Desconto (%)" type="number" min="0" max="100" step="0.01" :disabled="true" />
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
                <div class="flex items-center gap-2 mb-2">
                  <label class="flex items-center gap-2 text-sm">
                    <input type="checkbox" v-model="row.use_custom" class="form-checkbox" />
                    <span class="text-sm">Personalizado</span>
                  </label>
                </div>
                <div v-if="!row.use_custom">
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
                <div v-else>
                  <AppInput v-model="row.nome_produto" label="Nome do material" placeholder="Ex: Areia média" />
                </div>
              </div>
              <div class="md:col-span-2">
                <AppInput v-model="row.quantidade" :label="rowQuantityLabel(row)" type="number" min="0.001" step="0.001" />
              </div>
              <div class="md:col-span-2">
                <AppSelect
                  :model-value="row.unidade_venda"
                  :items="row.use_custom ? ALL_UNITS : rowUnits(row)"
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

        <AppAlert v-if="pdfError" variant="error">{{ pdfError }}</AppAlert>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="closeDialog">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-file-check-outline" :loading="saving">Gerar orçamento</AppButton>
        </div>
      </form>
    </AppModal>

    <AppModal v-model="confirmActionOpen" title="O que deseja fazer?" description="Escolha se quer criar o orçamento ou gerar um PDF como venda." max-width="sm">
      <div class="space-y-4">
        <div class="text-sm text-muted-foreground">Você pode apenas criar o orçamento para enviar ao cliente, ou gerar um PDF de venda (quando a venda já foi realizada).</div>
        <div class="flex justify-end gap-3 mt-4">
          <AppButton variant="outline" @click="confirmActionOpen = false">Cancelar</AppButton>
          <AppButton @click="performSave('orcamento')">Criar orçamento</AppButton>
          <AppButton color="success" @click="performSave('venda')">Gerar PDF de venda</AppButton>
        </div>
      </div>
    </AppModal>

    <AppConfirmDialog
      v-model="confirmDeleteOpen"
      title="Excluir orçamento"
      :description="confirmDeleteDescription"
      confirm-text="Excluir orçamento"
      :loading="deletingId !== null"
      @confirm="confirmRemove"
    >
      <p>Essa ação remove o orçamento selecionado. O PDF já baixado não será apagado do dispositivo do cliente.</p>
    </AppConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/client'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
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
const confirmActionOpen = ref(false)
const confirmDeleteOpen = ref(false)
const deletingId = ref<number | null>(null)
const itemPendingRemoval = ref<any | null>(null)
const downloadingPdfId = ref<number | null>(null)
const pdfError = ref('')

const form = ref<any>({})
const editingId = ref<number | null>(null)
const confirmDeleteDescription = computed(() => {
  const item = itemPendingRemoval.value
  if (!item) return 'Deseja excluir este orçamento?'
  return `Deseja excluir o orçamento de ${item.cliente_nome} no valor de ${formatBRL(item.valor_total)}?`
})

const totalBruto = computed(() =>
  (form.value.itens ?? []).reduce((total: number, row: any) => total + rowSubtotal(row), 0),
)

const descontoValor = computed(() => Number(form.value.desconto_valor ?? 0))

const descontoPercentual = computed({
  get() {
    const val = Number(form.value.desconto_valor ?? 0)
    if (!totalBruto.value) return 0
    return Number(((val / totalBruto.value) * 100).toFixed(2))
  },
  set(v: number) {
    const p = Number(v) || 0
    const pFixed = Number(p.toFixed(2))
    form.value.desconto_percentual = pFixed
    const valor = Number((totalBruto.value * pFixed) / 100)
    form.value.desconto_valor = Number(valor.toFixed(2))
  },
})

const descontoValorInput = computed({
  get() {
    return Number(form.value.desconto_valor ?? 0)
  },
  set(v: number) {
    let val = Number(v) || 0
    if (val < 0) val = 0
    if (val > totalBruto.value) val = totalBruto.value
    const valFixed = Number(val.toFixed(2))
    form.value.desconto_valor = valFixed
    const perc = totalBruto.value ? (valFixed / totalBruto.value) * 100 : 0
    form.value.desconto_percentual = Number(perc.toFixed(2))
  },
})

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
  const unidadeVenda = primeiroProduto?.unidade_medida ?? primeiroProduto?.unidade_estoque ?? null
  return {
    produto_id: primeiroProduto?.id ?? null,
    use_custom: false,
    nome_produto: '',
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
    desconto_valor: 0,
    observacao: '',
    itens: [createRow()],
  }
}

function getProduto(produtoId: unknown) {
  return produtos.value.find((produto) => produto.id === produtoId) ?? null
}

function rowMeasure(row: any) {
  const produto = getProduto(row.produto_id)
  // If a registered product is selected, show its commercial unit (unidade_medida) first
  if (produto) {
    const unidadeComercial = produto.unidade_medida ?? produto.unidade_estoque
    return getUnitLabel(unidadeComercial, row.quantidade) || '-'
  }
  // For custom items, show the selected unidade_venda if present
  if (row.unidade_venda) return getUnitLabel(row.unidade_venda, row.quantidade) || '-'
  return '-'
}

function rowUnits(row: any) {
  const produto = getProduto(row.produto_id)
  if (!produto) return []
  const units = new Set<string>((produto.precos_venda ?? []).filter((item: any) => item.ativo !== false).map((item: any) => String(item.unidade_venda)))
  // include commercial unit first, then estoque
  if (produto.unidade_medida) units.add(String(produto.unidade_medida))
  if (produto.unidade_estoque) units.add(String(produto.unidade_estoque))
  return Array.from(units).map((unit) => ({ title: getUnitLabel(unit), value: unit }))
}

const ALL_UNITS = [
  'KG',
  'UNIDADE',
  'LATA',
  'MILHEIRO',
  'CARRADA',
  'METRO',
  'METRO_QUADRADO',
  'METRO_CUBICO',
  'PACOTE',
].map((u) => ({ title: getUnitLabel(u), value: u }))

function rowQuantityLabel(row: any) {
  const produto = getProduto(row.produto_id)
  if (produto) return `Qtd (${getUnitLabel(produto.unidade_medida ?? produto.unidade_estoque)})`
  return row.unidade_venda ? `Qtd (${getUnitLabel(row.unidade_venda)})` : 'Qtd'
}

function rowSubtotal(row: any) {
  return Number(row.quantidade ?? 0) * Number(row.preco_unitario ?? 0)
}

function updateRowProduct(index: number, value: string | number | null) {
  const produtoId = value == null ? null : Number(value)
  const row = form.value.itens[index]
  row.produto_id = produtoId
  // selecting a registered product implies not using a custom free-text item
  if (produtoId !== null) row.use_custom = false
  const produto = getProduto(produtoId)
  row.unidade_venda = produto?.unidade_estoque ?? null
  row.preco_unitario = resolvePrice(produto, row.unidade_venda)
}

function updateRowUnit(index: number, value: string | number | null) {
  const row = form.value.itens[index]
  row.unidade_venda = value == null ? null : String(value)
  const produto = getProduto(row.produto_id)
  if (produto) {
    row.preco_unitario = resolvePrice(produto, row.unidade_venda)
  }
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
  editingId.value = null
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  reset()
  editingId.value = null
}

function openEdit(item: any) {
  editingId.value = item.id
  form.value = {
    cliente_nome: item.cliente_nome ?? '',
    validade_dias: item.validade_dias ?? 7,
    desconto_percentual: Number(item.desconto_percentual ?? 0),
    desconto_valor: Number(item.desconto_valor ?? 0),
    observacao: item.observacao ?? '',
    itens: (item.itens ?? []).map((it: any) => ({
      produto_id: it.produto?.id ?? null,
      use_custom: !it.produto,
      nome_produto: it.nome_produto ?? '',
      unidade_venda: it.unidade_venda,
      quantidade: Number(it.quantidade ?? 0),
      preco_unitario: Number(it.preco_unitario ?? 0),
    })),
  }
  dialogOpen.value = true
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
    desconto_percentual: String(descontoPercentual.value ?? 0),
    observacao: String(form.value.observacao ?? ''),
    itens: form.value.itens.map((row: any) => ({
      produto_id: row.use_custom ? undefined : Number(row.produto_id),
      nome_produto: row.use_custom ? String(row.nome_produto ?? '').trim() : undefined,
      quantidade: Number(row.quantidade ?? 0),
      unidade_venda: row.unidade_venda,
      preco_unitario: String(row.preco_unitario ?? 0),
    })),
  }

  saving.value = true
  try {
    if (editingId.value) {
      await api.patch(`/orcamentos/${editingId.value}/`, payload)
    } else {
      await api.post('/orcamentos/', payload)
    }
    await loadOrcamentos(0)
    closeDialog()
    editingId.value = null
  } finally {
    saving.value = false
  }
}

function openActionDialog() {
  confirmActionOpen.value = true
}

async function performSave(mode: 'orcamento' | 'venda') {
  const payload = {
    cliente_nome: String(form.value.cliente_nome ?? '').trim(),
    validade_dias: Number(form.value.validade_dias ?? 7),
    desconto_percentual: String(descontoPercentual.value ?? 0),
    observacao: String(form.value.observacao ?? ''),
    itens: form.value.itens.map((row: any) => ({
      produto_id: row.use_custom ? undefined : Number(row.produto_id),
      nome_produto: row.use_custom ? String(row.nome_produto ?? '').trim() : undefined,
      quantidade: Number(row.quantidade ?? 0),
      unidade_venda: row.unidade_venda,
      preco_unitario: String(row.preco_unitario ?? 0),
    })),
  }

  saving.value = true
  try {
    let data: any = null
    if (editingId.value) {
      const resp = await api.patch(`/orcamentos/${editingId.value}/`, payload)
      data = resp.data
    } else {
      const resp = await api.post('/orcamentos/', payload)
      data = resp.data
    }
    await loadOrcamentos(0)
    // close and then optionally download the PDF as a venda
    closeDialog()
    confirmActionOpen.value = false
    const docId = data?.id ?? editingId.value
    if (mode === 'venda' && docId) {
      await downloadPdf(docId, 'venda')
    }
    editingId.value = null
  } finally {
    saving.value = false
  }
}

async function downloadPdf(id: number, docType: 'orcamento' | 'venda' = 'orcamento') {
  downloadingPdfId.value = id
  pdfError.value = ''
  try {
    const urlPath = docType === 'venda' ? `/orcamentos/${id}/pdf/?type=venda` : `/orcamentos/${id}/pdf/`
    const response = await api.get(urlPath, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `${docType}-${id}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error: any) {
    pdfError.value =
      error?.response?.data?.detail ||
      'Não foi possível gerar o PDF agora. Verifique se o backend está com o ReportLab instalado.'
  } finally {
    downloadingPdfId.value = null
  }
}

function remove(item: any) {
  itemPendingRemoval.value = item
  confirmDeleteOpen.value = true
}

async function confirmRemove() {
  const item = itemPendingRemoval.value
  if (!item) return

  deletingId.value = item.id
  try {
    await api.delete(`/orcamentos/${item.id}/`)
    confirmDeleteOpen.value = false
    itemPendingRemoval.value = null
    await loadOrcamentos(2000)
  } finally {
    deletingId.value = null
  }
}

onMounted(async () => {
  await loadProdutos()
  reset()
  await loadOrcamentos(0)
})
</script>