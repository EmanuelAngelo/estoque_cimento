<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Vendas" description="Registro de vendas e baixa automática do estoque">
      <template #actions>
        <AppButton icon="mdi-plus" @click="openDialog">Nova venda</AppButton>
        <AppButton variant="outline" icon="mdi-refresh" @click="loadVendas">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Últimas vendas</div>
          <div class="app-card-subtitle">Histórico recente de vendas</div>
        </div>
      </div>

      <AppSpinner v-if="loadingVendas" />

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Cliente</th>
              <th>Tipo</th>
              <th class="text-right">Total</th>
              <th class="text-right">Lucro</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td class="text-muted-foreground">{{ formatDateTime(it.data_venda) }}</td>
              <td class="font-medium">{{ it.cliente_nome }}</td>
              <td>
                <span
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="it.tipo_saida === 'ENTREGA' ? 'bg-accent/10 text-accent' : 'bg-primary/10 text-primary'"
                >
                  {{ it.tipo_saida }}
                </span>
              </td>
              <td class="text-right font-medium">{{ formatBRL(it.valor_total_venda) }}</td>
              <td class="text-right font-medium text-success">{{ formatBRL(it.lucro_total_venda) }}</td>
              <td class="text-right">
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Editar"
                  @click="openEdit(it)"
                >
                  <span class="mdi mdi-pencil text-lg" />
                </button>
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Excluir"
                  @click="remove(it)"
                >
                  <span class="mdi mdi-trash-can-outline text-lg" />
                </button>
              </td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="6">
                <EmptyState
                  icon="mdi-cart-outline"
                  title="Sem vendas"
                  description="Clique em 'Nova venda' para registrar sua primeira venda."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal
      v-model="dialogOpen"
      :title="isEditing ? 'Editar venda' : 'Nova venda'"
      description="Informe cliente, material e valores"
      max-width="xl"
    >
      <form class="space-y-6" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-4">
            <AppInput
              v-model="form.cliente_nome"
              label="Cliente"
              placeholder="Nome do cliente"
              icon="mdi-account-outline"
              :error="fieldErrors.cliente_nome?.[0]"
            />
          </div>
          <div class="md:col-span-5">
            <AppSelect
              v-model="form.produto_id"
              :items="produtos"
              item-title="label"
              item-value="id"
              label="Material"
              icon="mdi-package-variant"
              :error="fieldErrors.produto_id?.[0]"
              :disabled="isEditing"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput
              v-model="form.quantidade"
              :label="quantidadeLabel"
              type="number"
              min="0.001"
              step="0.001"
              :error="fieldErrors.quantidade?.[0]"
              :disabled="isEditing"
            />
          </div>
          <div class="md:col-span-2">
            <AppSelect
              v-model="form.unidade_venda"
              :items="unidadesVendaDisponiveis"
              label="Unidade"
              :error="fieldErrors.unidade_venda?.[0]"
              :disabled="isEditing"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput :model-value="estoqueAtualFormatado" label="Estoque" readonly />
          </div>
          <div class="md:col-span-3">
            <AppInput :model-value="medidaSelecionada" label="Medida do item" readonly />
          </div>
          <div class="md:col-span-2">
            <AppInput :model-value="estoqueRestanteFormatado" label="Restante" readonly :error="!isEditing && estoqueRestante < 0 ? 'Estoque insuficiente' : ''" />
          </div>
          <div class="md:col-span-2">
            <AppSelect
              v-model="form.tipo_saida"
              :items="tiposSaida"
              label="Tipo"
              :error="fieldErrors.tipo_saida?.[0]"
            />
          </div>
          <div class="md:col-span-3">
            <AppInput
              v-model="form.data_venda"
              label="Data"
              type="datetime-local"
              icon="mdi-calendar"
              :error="fieldErrors.data_venda?.[0]"
            />
          </div>
          <div class="md:col-span-3">
            <AppInput
              v-model="form.valor_unitario_venda"
              label="Valor unit."
              type="number"
              min="0"
              step="0.01"
              :error="fieldErrors.valor_unitario_venda?.[0]"
            />
          </div>
          <div class="md:col-span-6">
            <AppTextarea v-model="form.observacao" label="Observação (opcional)" :rows="2" />
          </div>
        </div>

        <AppAlert v-if="apiError" variant="error">{{ apiError }}</AppAlert>

        <AppAlert v-if="!isEditing && estoqueRestante < 0" variant="warning">
          Quantidade maior que o estoque disponível. Reduza a quantidade.
        </AppAlert>

        <AppAlert variant="info">
          Total venda: <strong>{{ formatBRL(totalVenda) }}</strong> — Lucro:
          <strong>{{ formatBRL(totalLucroEstimado) }}</strong>
        </AppAlert>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="dialogOpen = false">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-plus" :loading="saving" :disabled="!canSubmit">Registrar</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/client'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import {
  convertProductQuantity,
  formatBRL,
  formatDateTime,
  formatMaterialLabel,
  formatMaterialMeasure,
  formatQuantityWithUnit,
  getUnitLabel,
  resolveProductSalePrice,
  resolveProductUnitCost,
} from '@/lib/formatters'

const tiposSaida = [
  { title: 'Retirada', value: 'RETIRADA' },
  { title: 'Entrega', value: 'ENTREGA' },
]

const produtos = ref<any[]>([])
const items = ref<any[]>([])
const loadingVendas = ref(false)

const form = ref<any>({
  cliente_nome: '',
  produto_id: null,
  quantidade: 1,
  unidade_venda: null,
  data_venda: new Date().toISOString().slice(0, 16),
  tipo_saida: 'RETIRADA',
  valor_unitario_venda: null,
  observacao: '',
})

const dialogOpen = ref(false)

const editingId = ref<number | null>(null)
const isEditing = computed(() => editingId.value != null)

const saving = ref(false)
const apiError = ref('')
const fieldErrors = ref<Record<string, string[]>>({})

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function clearErrors() {
  apiError.value = ''
  fieldErrors.value = {}
}

function validateForm() {
  const errors: Record<string, string[]> = {}

  if (!String(form.value.cliente_nome ?? '').trim()) {
    errors.cliente_nome = ['Obrigatório']
  }
  if (!form.value.produto_id) {
    errors.produto_id = ['Obrigatório']
  }
  if (Number(form.value.quantidade ?? 0) <= 0) {
    errors.quantidade = ['Informe uma quantidade maior que zero']
  }
  if (!form.value.unidade_venda) {
    errors.unidade_venda = ['Obrigatório']
  }
  if (!form.value.tipo_saida) {
    errors.tipo_saida = ['Obrigatório']
  }

  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

function setErrorsFromResponse(data: any) {
  // DRF usual shapes: {field: [msg]}, {non_field_errors: [msg]}, {detail: '...'}
  if (!data) {
    apiError.value = 'Não foi possível registrar a venda.'
    return
  }
  if (typeof data === 'string') {
    apiError.value = data
    return
  }
  if (typeof data?.detail === 'string') {
    apiError.value = data.detail
    return
  }
  if (Array.isArray(data?.non_field_errors) && data.non_field_errors.length) {
    apiError.value = String(data.non_field_errors[0])
  }

  const nextFieldErrors: Record<string, string[]> = {}
  for (const [key, value] of Object.entries(data)) {
    if (key === 'non_field_errors' || key === 'detail') continue
    if (Array.isArray(value)) nextFieldErrors[key] = value.map((v) => String(v))
    else if (typeof value === 'string') nextFieldErrors[key] = [value]
  }
  fieldErrors.value = nextFieldErrors

  if (!apiError.value) {
    const firstField = Object.keys(nextFieldErrors)[0]
    apiError.value = firstField ? nextFieldErrors[firstField]?.[0] ?? 'Verifique os campos.' : 'Verifique os campos.'
  }
}

function reset() {
  lastAutoPreco.value = null
  editingId.value = null
  form.value = {
    cliente_nome: '',
    produto_id: produtos.value.length ? produtos.value[0].id : null,
    quantidade: 1,
    unidade_venda: produtos.value.length ? produtos.value[0].unidade_estoque : null,
    data_venda: new Date().toISOString().slice(0, 16),
    tipo_saida: 'RETIRADA',
    valor_unitario_venda: null,
    observacao: '',
  }
}

function openDialog() {
  reset()
  clearErrors()
  // garante preenchimento do valor unitário na primeira abertura
  const p = produtoSelecionado.value
  if (p && (form.value.valor_unitario_venda == null || form.value.valor_unitario_venda === '')) {
    const autoPreco = resolveProductSalePrice(p, form.value.unidade_venda || p.unidade_estoque)
    form.value.valor_unitario_venda = autoPreco
    lastAutoPreco.value = autoPreco
  }
  dialogOpen.value = true
}

function openEdit(it: any) {
  const item = it?.itens?.[0]
  editingId.value = it.id
  form.value = {
    cliente_nome: it.cliente_nome ?? '',
    produto_id: item?.produto?.id ?? null,
    quantidade: item?.quantidade ?? 1,
    unidade_venda: item?.unidade_venda ?? item?.produto?.unidade_estoque ?? null,
    data_venda: it.data_venda ? new Date(it.data_venda).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
    tipo_saida: it.tipo_saida ?? 'RETIRADA',
    valor_unitario_venda: item?.preco_unitario != null ? Number(item.preco_unitario) : null,
    observacao: it.observacao ?? '',
  }
  clearErrors()
  dialogOpen.value = true
}

const produtoSelecionado = computed(() => produtos.value.find((p) => p.id === form.value.produto_id) ?? null)
const unidadesVendaDisponiveis = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return []
  const units = new Set<string>([String(produto.unidade_estoque)])
  if (produto.unidade_medida) units.add(String(produto.unidade_medida))
  for (const item of produto.precos_venda ?? []) {
    if (item?.ativo !== false && item?.unidade_venda) units.add(String(item.unidade_venda))
  }
  for (const conversao of produto.conversoes_unidade ?? []) {
    const origem = String(conversao?.unidade_origem ?? '')
    const destino = String(conversao?.unidade_destino ?? '')
    if (origem) units.add(origem)
    if (destino) units.add(destino)
  }
  return Array.from(units).map((unit) => ({ title: getUnitLabel(unit), value: unit }))
})

const estoqueAtual = computed(() => {
  const p = produtoSelecionado.value
  if (!p) return 0
  return Number(p.quantidade_estoque ?? 0)
})

const estoqueAtualFormatado = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return String(estoqueAtual.value)
  return formatQuantityWithUnit(estoqueAtual.value, produto.unidade_estoque, 3)
})

const medidaSelecionada = computed(() => formatMaterialMeasure(produtoSelecionado.value) || '-')

const quantidadeLabel = computed(() => {
  const produto = produtoSelecionado.value
  const unidade = form.value.unidade_venda || produto?.unidade_estoque
  return unidade ? `Qtd (${getUnitLabel(unidade)})` : 'Qtd'
})

const quantidadeEstoqueConsumida = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return 0
  const convertido = convertProductQuantity(
    produto,
    Number(form.value.quantidade ?? 0),
    form.value.unidade_venda || produto.unidade_estoque,
    produto.unidade_estoque,
  )
  return convertido ?? Number(form.value.quantidade ?? 0)
})

const estoqueRestante = computed(() => estoqueAtual.value - quantidadeEstoqueConsumida.value)

const estoqueRestanteFormatado = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return String(estoqueRestante.value)
  return formatQuantityWithUnit(estoqueRestante.value, produto.unidade_estoque, 3)
})

const canSubmit = computed(() => {
  if (saving.value) return false
  if (isEditing.value) return true
  return estoqueRestante.value >= 0
})

const lastAutoPreco = ref<number | null>(null)

watch(
  () => form.value.produto_id,
  () => {
    const p = produtoSelecionado.value
    if (p) {
      if (!isEditing.value) form.value.unidade_venda = p.unidade_estoque
      const nextPreco = resolveProductSalePrice(p, form.value.unidade_venda || p.unidade_estoque)
      const curPreco = form.value.valor_unitario_venda

      // Atualiza automaticamente quando vazio OU quando ainda estava no "automático" do produto anterior
      if (curPreco == null || curPreco === '' || Number(curPreco) === Number(lastAutoPreco.value)) {
        form.value.valor_unitario_venda = nextPreco
      }
      lastAutoPreco.value = nextPreco
    }
  },
)

watch(
  () => form.value.unidade_venda,
  () => {
    const p = produtoSelecionado.value
    if (!p) return
    const nextPreco = resolveProductSalePrice(p, form.value.unidade_venda || p.unidade_estoque)
    const curPreco = form.value.valor_unitario_venda
    if (curPreco == null || curPreco === '' || Number(curPreco) === Number(lastAutoPreco.value)) {
      form.value.valor_unitario_venda = nextPreco
    }
    lastAutoPreco.value = nextPreco
  },
)

watch(
  () => form.value.quantidade,
  () => {
    // mantém sempre numérico para o total reagir corretamente
    if (form.value.quantidade === '' || form.value.quantidade == null) return
    form.value.quantidade = Number(form.value.quantidade)
  },
)

const totalVenda = computed(() => Number(form.value.valor_unitario_venda ?? 0) * Number(form.value.quantidade ?? 0))

const custoUnitarioEstimado = computed(() => {
  const p = produtoSelecionado.value
  if (!p) return 0
  return resolveProductUnitCost(p, form.value.unidade_venda || p.unidade_estoque)
})

const totalLucroEstimado = computed(
  () => (Number(form.value.valor_unitario_venda ?? 0) - Number(custoUnitarioEstimado.value ?? 0)) * Number(form.value.quantidade ?? 0),
)

async function loadProdutos() {
  const { data } = await api.get('/produtos/?ativo=true&ordering=tipo_material,nome_produto')
  produtos.value = data.map((p: any) => ({ ...p, label: formatMaterialLabel(p) }))
  if (!form.value.produto_id && produtos.value.length) form.value.produto_id = produtos.value[0].id
  if (!form.value.unidade_venda && produtos.value.length) form.value.unidade_venda = produtos.value[0].unidade_estoque
  // se já tiver produto selecionado, garante valor unitário preenchido
  const p = produtos.value.find((x) => x.id === form.value.produto_id)
  if (p && (form.value.valor_unitario_venda == null || form.value.valor_unitario_venda === '')) {
    const autoPreco = resolveProductSalePrice(p, form.value.unidade_venda || p.unidade_estoque)
    form.value.valor_unitario_venda = autoPreco
    lastAutoPreco.value = autoPreco
  }
}

async function loadVendas(minDurationMs = 0) {
  const startedAt = Date.now()
  loadingVendas.value = true
  try {
    const { data } = await api.get('/vendas/?ordering=-data_venda')
    items.value = data
  } finally {
    const elapsed = Date.now() - startedAt
    if (elapsed < minDurationMs) await sleep(minDurationMs - elapsed)
    loadingVendas.value = false
  }
}

async function save() {
  const startedAt = Date.now()
  clearErrors()
  if (!validateForm()) return

  if (!canSubmit.value) {
    apiError.value = 'Quantidade maior que o estoque disponível.'
    return
  }

  const payload: any = { ...form.value }
  // Normalize payload to the serializer expectations
  payload.cliente_nome = String(payload.cliente_nome ?? '').trim()
  payload.produto_id = payload.produto_id != null ? Number(payload.produto_id) : null
  payload.quantidade = payload.quantidade != null ? String(payload.quantidade) : payload.quantidade
  payload.unidade_venda = payload.unidade_venda || produtoSelecionado.value?.unidade_estoque
  if (payload.data_venda) {
    const dt = new Date(payload.data_venda)
    if (!Number.isNaN(dt.getTime())) payload.data_venda = dt.toISOString()
  }
  if (payload.valor_unitario_venda != null && payload.valor_unitario_venda !== '') payload.valor_unitario_venda = String(payload.valor_unitario_venda)
  delete payload.custo_unitario_considerado

  saving.value = true
  try {
    if (isEditing.value && editingId.value != null) {
      await api.patch(`/vendas/${editingId.value}/`, {
        cliente_nome: payload.cliente_nome,
        data_venda: payload.data_venda,
        tipo_saida: payload.tipo_saida,
        observacao: payload.observacao,
        valor_unitario_venda: payload.valor_unitario_venda,
      })
    } else {
      await api.post('/vendas/', payload)
    }
    await loadProdutos()
    await loadVendas(0)
    const elapsed = Date.now() - startedAt
    if (elapsed < 2000) await sleep(2000 - elapsed)
    dialogOpen.value = false
    editingId.value = null
  } catch (e: any) {
    setErrorsFromResponse(e?.response?.data)
  } finally {
    saving.value = false
  }
}

async function remove(it: any) {
  if (!confirm('Excluir (cancelar) esta venda? Isso vai estornar no estoque.')) return
  await api.delete(`/vendas/${it.id}/`)
  await loadProdutos()
  await loadVendas(2000)
}

onMounted(async () => {
  await loadProdutos()
  await loadVendas(0)
})
</script>
