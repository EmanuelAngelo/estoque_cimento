<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Entradas de estoque" description="Registro de recebimento de mercadoria">
      <template #actions>
        <AppButton icon="mdi-plus" @click="openDialog">Nova entrada</AppButton>
        <AppButton variant="outline" icon="mdi-refresh" @click="loadEntradas">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Últimas entradas</div>
          <div class="app-card-subtitle">Histórico recente de recebimentos</div>
        </div>
      </div>

      <AppSpinner v-if="loadingEntradas" />

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Material</th>
              <th>Tipo</th>
              <th class="text-right">Qtd</th>
              <th class="text-right">Custo</th>
              <th>Usuário</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td class="text-muted-foreground">{{ formatDate(it.data_entrada) }}</td>
              <td class="font-medium">{{ formatMaterialLabel(it.produto) }}</td>
              <td class="text-muted-foreground">{{ it.produto?.tipo_material_label }}</td>
              <td class="text-right font-medium">{{ formatQuantidadeEntrada(it) }}</td>
              <td class="text-right">{{ formatBRL(it.custo_unitario_fabrica) }}</td>
              <td class="text-muted-foreground">{{ it.usuario_responsavel }}</td>
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
              <td colspan="7">
                <EmptyState
                  icon="mdi-tray-arrow-down"
                  title="Sem entradas"
                  description="Clique em 'Nova entrada' para registrar um recebimento de material."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal
      v-model="dialogOpen"
      :title="isEditing ? 'Editar entrada' : 'Nova entrada'"
      description="Preencha os dados do recebimento"
      max-width="xl"
    >
      <form class="space-y-6" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-6">
            <AppSelect
              v-model="form.produto_id"
              :items="produtos"
              item-title="label"
              item-value="id"
              label="Material"
              :disabled="isEditing"
              icon="mdi-package-variant"
            />
          </div>
          <div class="md:col-span-2">
            <AppSelect
              v-model="form.unidade_entrada"
              :items="unidadesEntradaDisponiveis"
              label="Unidade entrada"
              :disabled="isEditing"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput
              v-model="form.quantidade"
              :label="quantidadeLabel"
              type="number"
              :disabled="isEditing"
              min="0.001"
              step="0.001"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput
              v-model="form.custo_unitario_fabrica"
              label="Custo unit. (fábrica)"
              type="number"
              :disabled="isEditing"
              min="0"
              step="0.01"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput v-model="form.data_entrada" label="Data" type="date" />
          </div>
          <div class="md:col-span-2">
            <AppInput :model-value="quantidadeEstoquePrevista" label="Baixa no estoque" readonly />
          </div>
          <div class="md:col-span-4">
            <AppInput v-model="form.fornecedor" label="Fornecedor (opcional)" placeholder="Nome do fornecedor" />
          </div>
          <div class="md:col-span-6">
            <AppTextarea v-model="form.observacao" label="Observação (opcional)" :rows="2" />
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="closeDialog">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-plus" :loading="saving">Registrar</AppButton>
        </div>
      </form>
    </AppModal>

    <AppConfirmDialog
      v-model="confirmDeleteOpen"
      title="Cancelar entrada"
      :description="confirmDeleteDescription"
      confirm-text="Cancelar entrada"
      :loading="deletingId !== null"
      @confirm="confirmRemove"
    >
      <p>Ao confirmar, o sistema estorna essa entrada do estoque e mantém o histórico da movimentação.</p>
    </AppConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { convertProductQuantity, formatBRL, formatDate, formatMaterialLabel, formatQuantityWithUnit, getUnitLabel } from '@/lib/formatters'

const produtos = ref<any[]>([])
const items = ref<any[]>([])
const loadingEntradas = ref(false)
const saving = ref(false)
const confirmDeleteOpen = ref(false)
const deletingId = ref<number | null>(null)
const itemPendingRemoval = ref<any | null>(null)

const form = ref<any>({
  produto_id: null,
  quantidade: 1,
  custo_unitario_fabrica: null,
  data_entrada: new Date().toISOString().slice(0, 10),
  fornecedor: '',
  observacao: '',
})

const dialogOpen = ref(false)

const editingId = ref<number | null>(null)
const isEditing = computed(() => editingId.value != null)
const confirmDeleteDescription = computed(() => {
  const item = itemPendingRemoval.value
  if (!item) return 'Deseja cancelar esta entrada?'
  return `Deseja cancelar a entrada de ${formatMaterialLabel(item.produto)} em ${formatDate(item.data_entrada)}?`
})

const lastAutoCost = ref<number | null>(null)
const produtoSelecionado = computed(() => produtos.value.find((p) => p.id === form.value.produto_id) ?? null)
const unidadesEntradaDisponiveis = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return []
  const baseUnit = String(produto.unidade_estoque)
  const units = new Set<string>([baseUnit])
  for (const conversao of produto.conversoes_unidade ?? []) {
    if (String(conversao.unidade_destino) === baseUnit) units.add(String(conversao.unidade_origem))
  }
  return Array.from(units).map((unit) => ({ title: getUnitLabel(unit), value: unit }))
})

const quantidadeEstoquePrevista = computed(() => {
  const produto = produtoSelecionado.value
  if (!produto) return '-'
  const converted = convertProductQuantity(
    produto,
    Number(form.value.quantidade ?? 0),
    form.value.unidade_entrada || produto.unidade_estoque,
    produto.unidade_estoque,
  )
  if (converted == null) return '-'
  return formatQuantityWithUnit(converted, produto.unidade_estoque, 3)
})

const quantidadeLabel = computed(() => {
  const produto = produtoSelecionado.value
  const unidade = form.value.unidade_entrada || produto?.unidade_estoque
  return unidade ? `Quantidade (${getUnitLabel(unidade)})` : 'Quantidade'
})

function formatQuantidadeEntrada(item: any) {
  return formatQuantityWithUnit(item?.quantidade, item?.unidade_entrada || item?.produto?.unidade_estoque)
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchEntradas() {
  const { data } = await api.get('/entradas/?ordering=-data_entrada')
  items.value = data
}

function applyAutoCost() {
  const p = produtoSelecionado.value
  if (!p) return
  const next = Number(p.custo_unitario_fabrica)
  const current = Number(form.value.custo_unitario_fabrica ?? 0)
  // Preenche automaticamente quando estiver vazio/0 ou quando o usuário ainda não alterou manualmente
  if (!current || lastAutoCost.value === null || current === lastAutoCost.value) {
    form.value.custo_unitario_fabrica = next
  }
  lastAutoCost.value = next
}

function reset() {
  lastAutoCost.value = null
  form.value = {
    produto_id: produtos.value.length ? produtos.value[0].id : null,
    unidade_entrada: produtos.value.length ? produtos.value[0].unidade_estoque : null,
    quantidade: 1,
    custo_unitario_fabrica: null,
    data_entrada: new Date().toISOString().slice(0, 10),
    fornecedor: '',
    observacao: '',
  }
}

function openDialog() {
  reset()
  applyAutoCost()
  editingId.value = null
  dialogOpen.value = true
}

function openEdit(it: any) {
  editingId.value = it.id
  form.value = {
    produto_id: it.produto?.id ?? null,
    unidade_entrada: it.unidade_entrada ?? it.produto?.unidade_estoque ?? null,
    quantidade: it.quantidade,
    custo_unitario_fabrica: it.custo_unitario_fabrica,
    data_entrada: it.data_entrada,
    fornecedor: it.fornecedor ?? '',
    observacao: it.observacao ?? '',
  }
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  editingId.value = null
  reset()
}

async function loadProdutos() {
  const { data } = await api.get('/produtos/?ativo=true&ordering=tipo_material,nome_produto')
  produtos.value = data.map((p: any) => ({ ...p, label: formatMaterialLabel(p) }))
  if (!form.value.produto_id && produtos.value.length) form.value.produto_id = produtos.value[0].id
  if (!form.value.unidade_entrada && produtos.value.length) form.value.unidade_entrada = produtos.value[0].unidade_estoque
  applyAutoCost()
}

watch(
  () => form.value.produto_id,
  () => {
    const produto = produtoSelecionado.value
    if (produto && !isEditing.value) form.value.unidade_entrada = produto.unidade_estoque
    applyAutoCost()
  },
)

async function loadEntradas(minDurationMs = 0) {
  const startedAt = Date.now()
  loadingEntradas.value = true
  try {
    await fetchEntradas()
  } finally {
    const elapsed = Date.now() - startedAt
    if (elapsed < minDurationMs) await sleep(minDurationMs - elapsed)
    loadingEntradas.value = false
  }
}

async function save() {
  const startedAt = Date.now()
  saving.value = true
  try {
    if (isEditing.value && editingId.value != null) {
      await api.patch(`/entradas/${editingId.value}/`, {
        data_entrada: form.value.data_entrada,
        fornecedor: form.value.fornecedor,
        observacao: form.value.observacao,
      })
    } else {
      const payload: any = { ...form.value }
      payload.produto_id = payload.produto_id != null ? Number(payload.produto_id) : null
      payload.quantidade = payload.quantidade != null ? String(payload.quantidade) : payload.quantidade
      payload.unidade_entrada = payload.unidade_entrada || produtoSelecionado.value?.unidade_estoque
      if (payload.custo_unitario_fabrica == null || payload.custo_unitario_fabrica === '') {
        delete payload.custo_unitario_fabrica
      } else {
        payload.custo_unitario_fabrica = String(payload.custo_unitario_fabrica)
      }
      await api.post('/entradas/', payload)
    }

    await loadEntradas()
    const elapsed = Date.now() - startedAt
    if (elapsed < 2000) await sleep(2000 - elapsed)
    closeDialog()
  } finally {
    saving.value = false
  }
}

function remove(it: any) {
  itemPendingRemoval.value = it
  confirmDeleteOpen.value = true
}

async function confirmRemove() {
  const item = itemPendingRemoval.value
  if (!item) return

  deletingId.value = item.id
  try {
    await api.delete(`/entradas/${item.id}/`)
    confirmDeleteOpen.value = false
    itemPendingRemoval.value = null
    await loadEntradas(2000)
  } finally {
    deletingId.value = null
  }
}

onMounted(async () => {
  await loadProdutos()
  await loadEntradas()
})
</script>
