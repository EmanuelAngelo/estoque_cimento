<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Entradas de estoque" description="Registro de recebimento de mercadoria">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog">Nova entrada</v-btn>
        <v-btn variant="outlined" prepend-icon="mdi-refresh" @click="loadEntradas">Atualizar</v-btn>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Últimas entradas</div>
          <div class="app-card-subtitle">Histórico recente de recebimentos</div>
        </div>
      </div>

      <div v-if="loadingEntradas" class="p-10 flex items-center justify-center">
        <v-progress-circular color="primary" indeterminate></v-progress-circular>
      </div>

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

    <v-dialog v-model="dialogOpen" max-width="980">
      <v-card class="overflow-hidden rounded-[var(--radius)]" elevation="0">
        <div class="px-6 py-5 bg-card border-b border-border">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-lg font-semibold text-foreground">Nova entrada</h2>
              <p class="text-sm text-muted-foreground mt-1">Preencha os dados do recebimento</p>
            </div>
            <v-btn icon="mdi-close" variant="text" @click="closeDialog" />
          </div>
        </div>

        <div class="p-6">
          <v-form @submit.prevent="save">
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  :items="produtos"
                  item-title="label"
                  item-value="id"
                  v-model="form.produto_id"
                  label="Produto"
                  :disabled="isEditing"
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field v-model.number="form.quantidade" label="Quantidade" type="number" :disabled="isEditing" />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field
                  v-model="form.custo_unitario_fabrica"
                  label="Custo unit. (fábrica)"
                  type="number"
                  :disabled="isEditing"
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field v-model="form.data_entrada" label="Data" type="date" />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field v-model="form.fornecedor" label="Fornecedor (opcional)" />
              </v-col>
              <v-col cols="12" md="8">
                <v-text-field v-model="form.observacao" label="Observação (opcional)" />
              </v-col>
            </v-row>

            <div class="mt-6 pt-4 border-t border-border flex justify-end gap-3">
              <v-btn variant="outlined" @click="closeDialog">Cancelar</v-btn>
              <v-btn color="primary" type="submit" prepend-icon="mdi-plus" :loading="saving" :disabled="saving">
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
