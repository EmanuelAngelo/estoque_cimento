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
              <th>Produto</th>
              <th>Marca</th>
              <th class="text-right">Qtd</th>
              <th class="text-right">Custo</th>
              <th>Usuário</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td class="text-muted-foreground">{{ formatDate(it.data_entrada) }}</td>
              <td class="font-medium">{{ it.produto?.nome_produto }}</td>
              <td class="text-muted-foreground">{{ it.produto?.marca }}</td>
              <td class="text-right font-medium">{{ it.quantidade }}</td>
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
                  description="Clique em 'Nova entrada' para registrar um recebimento."
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
              label="Produto"
              :disabled="isEditing"
              icon="mdi-package-variant"
            />
          </div>
          <div class="md:col-span-2">
            <AppInput v-model="form.quantidade" label="Quantidade" type="number" :disabled="isEditing" min="1" />
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
          <div class="md:col-span-4">
            <AppInput v-model="form.fornecedor" label="Fornecedor (opcional)" placeholder="Nome do fornecedor" />
          </div>
          <div class="md:col-span-8">
            <AppTextarea v-model="form.observacao" label="Observação (opcional)" :rows="2" />
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="closeDialog">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-plus" :loading="saving">Registrar</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTextarea from '@/components/ui/AppTextarea.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL, formatDate } from '@/lib/formatters'

const produtos = ref<any[]>([])
const items = ref<any[]>([])
const loadingEntradas = ref(false)
const saving = ref(false)

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

const lastAutoCost = ref<number | null>(null)
const produtoSelecionado = computed(() => produtos.value.find((p) => p.id === form.value.produto_id) ?? null)

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
  const { data } = await api.get('/produtos/?ativo=true&ordering=marca,nome_produto')
  produtos.value = data.map((p: any) => ({ ...p, label: `${p.marca} - ${p.nome_produto}` }))
  if (!form.value.produto_id && produtos.value.length) form.value.produto_id = produtos.value[0].id
  applyAutoCost()
}

watch(
  () => form.value.produto_id,
  () => applyAutoCost(),
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
      payload.quantidade = payload.quantidade != null ? Number(payload.quantidade) : payload.quantidade
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

async function remove(it: any) {
  if (!confirm('Excluir (cancelar) esta entrada? Isso vai estornar do estoque.')) return
  await api.delete(`/entradas/${it.id}/`)
  await loadEntradas(2000)
}

onMounted(async () => {
  await loadProdutos()
  await loadEntradas()
})
</script>
