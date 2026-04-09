<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Movimentações" description="Histórico de entradas e saídas">
      <template #actions>
        <AppButton variant="outline" icon="mdi-refresh" @click="load" :loading="loading">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card mb-6">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Filtros</div>
          <div class="app-card-subtitle">Refine o período e tipo de movimentação</div>
        </div>
      </div>
      <div class="app-card-body">
        <div class="grid gap-4 md:grid-cols-4">
          <AppInput v-model="filtro.data_inicial" label="Data inicial" type="datetime-local" />
          <AppInput v-model="filtro.data_final" label="Data final" type="datetime-local" />
          <AppSelect v-model="filtro.tipo" :items="tipos" label="Tipo" placeholder="Todos" />
          <div class="flex items-end justify-end">
            <AppButton icon="mdi-filter" @click="load" :loading="loading">Filtrar</AppButton>
          </div>
        </div>
      </div>
    </div>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Resultados</div>
          <div class="app-card-subtitle">Entradas e saídas registradas</div>
        </div>
      </div>

      <AppSpinner v-if="loading" />

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Produto</th>
              <th>Marca</th>
              <th>Tipo</th>
              <th class="text-right">Qtd</th>
              <th>Ref</th>
              <th class="text-right">Ref ID</th>
              <th>Usuário</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td class="text-muted-foreground">{{ formatDateTime(it.data_movimentacao) }}</td>
              <td class="font-medium">{{ it.produto?.nome_produto }}</td>
              <td class="text-muted-foreground">{{ it.produto?.marca }}</td>
              <td>
                <span
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                  :class="it.tipo_movimentacao === 'ENTRADA' ? 'bg-success/10 text-success' : 'bg-accent/10 text-accent'"
                >
                  {{ it.tipo_movimentacao }}
                </span>
              </td>
              <td class="text-right font-medium">{{ formatQuantity(it.quantidade) }}</td>
              <td class="text-muted-foreground">{{ it.referencia_tipo }}</td>
              <td class="text-right text-muted-foreground">{{ it.referencia_id }}</td>
              <td class="text-muted-foreground">{{ it.usuario_responsavel }}</td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="8">
                <EmptyState
                  icon="mdi-swap-horizontal"
                  title="Nenhum resultado"
                  description="Ajuste os filtros e clique em Filtrar."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatDateTime, formatQuantity } from '@/lib/formatters'

const tipos = [
  { title: 'Entrada', value: 'ENTRADA' },
  { title: 'Saída', value: 'SAIDA' },
]

const filtro = ref<any>({
  data_inicial: '',
  data_final: '',
  tipo: null,
})

const items = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filtro.value.data_inicial) params.set('data_inicial', new Date(filtro.value.data_inicial).toISOString())
    if (filtro.value.data_final) params.set('data_final', new Date(filtro.value.data_final).toISOString())
    if (filtro.value.tipo) params.set('tipo', String(filtro.value.tipo))

    const { data } = await api.get(`/movimentacoes/?${params.toString()}`)
    items.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
