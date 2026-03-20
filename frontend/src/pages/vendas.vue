<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Vendas" description="Registro de vendas e baixa automática do estoque">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog">Nova venda</v-btn>
        <v-btn variant="outlined" prepend-icon="mdi-refresh" @click="loadVendas">Atualizar</v-btn>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Últimas vendas</div>
          <div class="app-card-subtitle">Histórico recente de vendas</div>
        </div>
      </div>

      <div v-if="loadingVendas" class="p-10 flex items-center justify-center">
        <v-progress-circular color="primary" indeterminate></v-progress-circular>
      </div>

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

    <v-dialog v-model="dialogOpen" max-width="980">
      <v-card class="overflow-hidden rounded-[var(--radius)]" elevation="0">
        <div class="px-6 py-5 bg-card border-b border-border">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-lg font-semibold text-foreground">Nova venda</h2>
              <p class="text-sm text-muted-foreground mt-1">Informe cliente, produto e valores</p>
            </div>
            <v-btn icon="mdi-close" variant="text" @click="dialogOpen = false" />
          </div>
        </div>

        <div class="p-6">
          <v-form ref="formRef" @submit.prevent="save">
            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="form.cliente_nome"
                  label="Cliente"
                  prepend-inner-icon="mdi-account"
                  :rules="[rules.required]"
                  :error-messages="fieldErrors.cliente_nome"
                />
              </v-col>
              <v-col cols="12" md="5">
                <v-select
                  :items="produtos"
                  item-title="label"
                  item-value="id"
                  v-model="form.produto_id"
                  label="Produto"
                  prepend-inner-icon="mdi-package-variant"
                  :rules="[rules.required]"
                  :error-messages="fieldErrors.produto_id"
                  :disabled="isEditing"
                />
              </v-col>
              <v-col cols="12" md="1">
                <v-text-field
                  v-model.number="form.quantidade"
                  label="Qtd"
                  type="number"
                  :rules="[rules.min1]"
                  :error-messages="fieldErrors.quantidade"
                  :disabled="isEditing"
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field :model-value="String(estoqueAtual)" label="Estoque" readonly />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field
                  :model-value="String(estoqueRestante)"
                  label="Restante"
                  readonly
                  :color="estoqueRestante < 0 ? 'error' : undefined"
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-select
                  :items="tiposSaida"
                  item-title="title"
                  item-value="value"
                  v-model="form.tipo_saida"
                  label="Tipo"
                  :error-messages="fieldErrors.tipo_saida"
                />
              </v-col>

              <v-col cols="12" md="3">
                <v-text-field
                  v-model="form.data_venda"
                  label="Data"
                  type="datetime-local"
                  prepend-inner-icon="mdi-calendar"
                  :error-messages="fieldErrors.data_venda"
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="form.valor_unitario_venda"
                  label="Valor unit."
                  type="number"
                  :error-messages="fieldErrors.valor_unitario_venda"
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model="form.observacao" label="Observação (opcional)" />
              </v-col>

              <v-col cols="12" v-if="apiError">
                <v-alert type="error" variant="tonal">{{ apiError }}</v-alert>
              </v-col>

              <v-col cols="12" v-if="!isEditing && estoqueRestante < 0">
                <v-alert type="warning" variant="tonal">
                  Quantidade maior que o estoque disponível. Reduza a quantidade.
                </v-alert>
              </v-col>

              <v-col cols="12">
                <v-alert type="info" variant="tonal">
                  Total venda: <strong>{{ formatBRL(totalVenda) }}</strong> — Lucro:
                  <strong>{{ formatBRL(totalLucroEstimado) }}</strong>
                </v-alert>
              </v-col>
            </v-row>

            <div class="mt-6 pt-4 border-t border-border flex justify-end gap-3">
              <v-btn variant="outlined" @click="dialogOpen = false">Cancelar</v-btn>
              <v-btn color="primary" type="submit" prepend-icon="mdi-plus" :loading="saving" :disabled="!canSubmit">
                Registrar
              </v-btn>
            </div>
          </v-form>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/client'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL, formatDateTime } from '@/lib/formatters'

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
  data_venda: new Date().toISOString().slice(0, 16),
  tipo_saida: 'RETIRADA',
  valor_unitario_venda: null,
  observacao: '',
})

const dialogOpen = ref(false)

const editingId = ref<number | null>(null)
const isEditing = computed(() => editingId.value != null)

const formRef = ref<any>(null)
const saving = ref(false)
const apiError = ref('')
const fieldErrors = ref<Record<string, string[]>>({})

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

const rules = {
  required: (v: any) => !!String(v ?? '').trim() || 'Obrigatório',
  min1: (v: any) => Number(v ?? 0) >= 1 || 'Mínimo 1',
}

function clearErrors() {
  apiError.value = ''
  fieldErrors.value = {}
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
    form.value.valor_unitario_venda = Number(p.preco_unitario_loja)
    lastAutoPreco.value = Number(p.preco_unitario_loja)
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
    data_venda: it.data_venda ? new Date(it.data_venda).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
    tipo_saida: it.tipo_saida ?? 'RETIRADA',
    valor_unitario_venda: item?.preco_unitario != null ? Number(item.preco_unitario) : null,
    observacao: it.observacao ?? '',
  }
  clearErrors()
  dialogOpen.value = true
}

const produtoSelecionado = computed(() => produtos.value.find((p) => p.id === form.value.produto_id) ?? null)

const estoqueAtual = computed(() => {
  const p = produtoSelecionado.value
  if (!p) return 0
  return Number(p.quantidade_estoque ?? 0)
})

const estoqueRestante = computed(() => estoqueAtual.value - Number(form.value.quantidade ?? 0))

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
      const nextPreco = Number(p.preco_unitario_loja)
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
  const medio = Number(p.custo_medio_estoque ?? 0)
  return medio > 0 ? medio : Number(p.custo_unitario_fabrica ?? 0)
})

const totalLucroEstimado = computed(
  () => (Number(form.value.valor_unitario_venda ?? 0) - Number(custoUnitarioEstimado.value ?? 0)) * Number(form.value.quantidade ?? 0),
)

async function loadProdutos() {
  const { data } = await api.get('/produtos/?ativo=true&ordering=marca,nome_produto')
  produtos.value = data.map((p: any) => ({ ...p, label: `${p.marca} - ${p.nome_produto}` }))
  if (!form.value.produto_id && produtos.value.length) form.value.produto_id = produtos.value[0].id
  // se já tiver produto selecionado, garante valor unitário preenchido
  const p = produtos.value.find((x) => x.id === form.value.produto_id)
  if (p && (form.value.valor_unitario_venda == null || form.value.valor_unitario_venda === '')) {
    form.value.valor_unitario_venda = Number(p.preco_unitario_loja)
    lastAutoPreco.value = Number(p.preco_unitario_loja)
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
  const validation = await formRef.value?.validate?.()
  if (validation && validation.valid === false) return

  if (!canSubmit.value) {
    apiError.value = 'Quantidade maior que o estoque disponível.'
    return
  }

  const payload: any = { ...form.value }
  // Normalize payload to the serializer expectations
  payload.cliente_nome = String(payload.cliente_nome ?? '').trim()
  payload.produto_id = payload.produto_id != null ? Number(payload.produto_id) : null
  payload.quantidade = payload.quantidade != null ? Number(payload.quantidade) : payload.quantidade
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
