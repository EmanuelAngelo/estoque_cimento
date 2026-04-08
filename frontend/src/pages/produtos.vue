<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Cimentos" description="Cadastro e manutenção de produtos">
      <template #actions>
        <AppButton icon="mdi-plus" @click="openCreate">Novo cimento</AppButton>
        <AppButton variant="outline" icon="mdi-refresh" @click="load">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Lista de produtos</div>
          <div class="app-card-subtitle">Gerencie preços e status (ativo/inativo)</div>
        </div>
      </div>

      <AppSpinner v-if="loading" />

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

    <AppModal v-model="dialogOpen" :title="form.id ? 'Editar cimento' : 'Novo cimento'" description="Dados do produto e precificação" max-width="xl">
      <form class="space-y-6" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-3">
            <AppSelect v-model="form.marca" :items="marcas" label="Marca" />
          </div>
          <div class="md:col-span-5">
            <AppInput v-model="form.nome_produto" label="Nome" placeholder="Ex: CP-II 50kg" />
          </div>
          <div class="md:col-span-4">
            <AppInput v-model="form.descricao_produto" label="Descrição" placeholder="Descrição do produto" />
          </div>
          <div class="md:col-span-2">
            <AppInput v-model="form.peso_kg" label="Peso (kg)" type="number" min="0" step="0.001" />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="form.custo_unitario_fabrica" label="Custo fábrica" type="number" min="0" step="0.01" />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="form.preco_unitario_loja" label="Preço loja" type="number" min="0" step="0.01" />
          </div>
          <div class="md:col-span-4 flex items-end">
            <label class="flex h-11 w-full items-center justify-between rounded-[var(--radius)] border border-border bg-background px-4">
              <span class="text-sm font-medium text-foreground">Produto ativo</span>
              <button
                type="button"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                :class="form.ativo ? 'bg-primary' : 'bg-muted'"
                @click="form.ativo = !form.ativo"
              >
                <span
                  class="inline-block h-5 w-5 transform rounded-full bg-white transition"
                  :class="form.ativo ? 'translate-x-5' : 'translate-x-1'"
                />
              </button>
            </label>
          </div>
        </div>

        <div class="flex justify-end gap-3 border-t border-border pt-4">
          <AppButton variant="outline" @click="closeDialog">Cancelar</AppButton>
          <AppButton type="submit" icon="mdi-content-save" :loading="saving">
            {{ form.id ? 'Salvar' : 'Cadastrar' }}
          </AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
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

function normalizePayload() {
  return {
    ...form.value,
    peso_kg: Number(form.value.peso_kg ?? 0),
    custo_unitario_fabrica: Number(form.value.custo_unitario_fabrica ?? 0),
    preco_unitario_loja: Number(form.value.preco_unitario_loja ?? 0),
  }
}

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
    const payload = normalizePayload()
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
