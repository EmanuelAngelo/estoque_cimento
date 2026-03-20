<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Cimentos" description="Cadastro e manutenção de produtos">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">Novo cimento</v-btn>
        <v-btn variant="outlined" prepend-icon="mdi-refresh" @click="load">Atualizar</v-btn>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Lista de produtos</div>
          <div class="app-card-subtitle">Gerencie preços e status (ativo/inativo)</div>
        </div>
      </div>

      <div v-if="loading" class="p-10 flex items-center justify-center">
        <v-progress-circular color="primary" indeterminate></v-progress-circular>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Marca</th>
              <th>Nome</th>
              <th class="text-right">Peso</th>
              <th class="text-right">Custo</th>
              <th class="text-right">Preço</th>
              <th class="text-right">Lucro</th>
              <th>Status</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="text-muted-foreground">{{ item.marca }}</td>
              <td class="font-medium">{{ item.nome_produto }}</td>
              <td class="text-right">{{ item.peso_kg }}kg</td>
              <td class="text-right">{{ formatBRL(item.custo_unitario_fabrica) }}</td>
              <td class="text-right font-medium">{{ formatBRL(item.preco_unitario_loja) }}</td>
              <td class="text-right font-medium text-success">{{ formatBRL(item.lucro_unitario) }}</td>
              <td>
                <span
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="item.ativo ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'"
                >
                  {{ item.ativo ? 'Ativo' : 'Inativo' }}
                </span>
              </td>
              <td class="text-right">
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
                <button
                  type="button"
                  class="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  :aria-label="item.ativo ? 'Inativar' : 'Ativar'"
                  @click="toggleAtivo(item)"
                >
                  <span :class="['mdi', item.ativo ? 'mdi-eye-off-outline' : 'mdi-eye-outline', 'text-lg']" />
                </button>
              </td>
            </tr>

            <tr v-if="!items.length">
              <td colspan="8">
                <EmptyState
                  icon="mdi-cube-outline"
                  title="Sem produtos cadastrados"
                  description="Clique em 'Novo cimento' para cadastrar o primeiro produto."
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
              <h2 class="text-lg font-semibold text-foreground">
                {{ form.id ? 'Editar cimento' : 'Novo cimento' }}
              </h2>
              <p class="text-sm text-muted-foreground mt-1">Dados do produto e precificação</p>
            </div>
            <v-btn icon="mdi-close" variant="text" @click="closeDialog" />
          </div>
        </div>

        <div class="p-6">
          <v-form @submit.prevent="save">
            <v-row>
              <v-col cols="12" md="3">
                <v-select :items="marcas" v-model="form.marca" label="Marca" />
              </v-col>
              <v-col cols="12" md="5">
                <v-text-field v-model="form.nome_produto" label="Nome" />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field v-model="form.descricao_produto" label="Descrição" />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field v-model.number="form.peso_kg" label="Peso (kg)" type="number" />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model.number="form.custo_unitario_fabrica" label="Custo fábrica" type="number" />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field v-model.number="form.preco_unitario_loja" label="Preço loja" type="number" />
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center">
                <v-switch v-model="form.ativo" label="Ativo" inset hide-details />
              </v-col>
            </v-row>

            <div class="mt-6 pt-4 border-t border-border flex justify-end gap-3">
              <v-btn variant="outlined" @click="closeDialog">Cancelar</v-btn>
              <v-btn color="primary" type="submit" prepend-icon="mdi-content-save" :loading="saving" :disabled="saving">
                {{ form.id ? 'Salvar' : 'Cadastrar' }}
              </v-btn>
            </div>
          </v-form>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api/client'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL } from '@/lib/formatters'

const marcas = [
  { title: 'Itaqui', value: 'ITAQUI' },
  { title: 'Bravo', value: 'BRAVO' },
  { title: 'Poty', value: 'POTY' },
  { title: 'Monte Carlos', value: 'MONTE_CARLOS' },
]

const items = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const form = ref<any>({
  id: null,
  marca: 'ITAQUI',
  nome_produto: '',
  descricao_produto: '',
  peso_kg: 50,
  custo_unitario_fabrica: 0,
  preco_unitario_loja: 0,
  ativo: true,
})

const dialogOpen = ref(false)

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchItems() {
  const { data } = await api.get('/produtos/?ordering=marca,nome_produto')
  items.value = data
}

function reset() {
  form.value = {
    id: null,
    marca: 'ITAQUI',
    nome_produto: '',
    descricao_produto: '',
    peso_kg: 50,
    custo_unitario_fabrica: 0,
    preco_unitario_loja: 0,
    ativo: true,
  }
}

async function load(minDurationMs = 0) {
  const startedAt = Date.now()
  loading.value = true
  try {
    await fetchItems()
  } finally {
    const elapsed = Date.now() - startedAt
    if (elapsed < minDurationMs) await sleep(minDurationMs - elapsed)
    loading.value = false
  }
}

function openCreate() {
  reset()
  dialogOpen.value = true
}

function openEdit(item: any) {
  form.value = { ...item }
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  reset()
}

async function save() {
  const startedAt = Date.now()
  saving.value = true
  try {
    const payload = { ...form.value }
    if (payload.id) {
      await api.put(`/produtos/${payload.id}/`, payload)
    } else {
      await api.post('/produtos/', payload)
    }
    await load(0)
    const elapsed = Date.now() - startedAt
    if (elapsed < 2000) await sleep(2000 - elapsed)
    dialogOpen.value = false
    reset()
  } finally {
    saving.value = false
  }
}

async function toggleAtivo(item: any) {
  await api.patch(`/produtos/${item.id}/`, { ativo: !item.ativo })
  await load(2000)
}

async function remove(item: any) {
  if (!confirm('Excluir este produto? Pode falhar se já houver entradas/vendas.')) return
  await api.delete(`/produtos/${item.id}/`)
  await load(2000)
}

onMounted(load)
</script>
