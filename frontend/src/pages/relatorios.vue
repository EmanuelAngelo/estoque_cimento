<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Relatórios" description="Vendas e lucro por período/cliente/marca">
      <template #actions>
        <v-btn color="primary" prepend-icon="mdi-chart-box-outline" @click="load" :loading="loading">Gerar</v-btn>
      </template>
    </PageHeader>

    <div class="app-card mb-6">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Filtros</div>
          <div class="app-card-subtitle">Defina o intervalo e critérios</div>
        </div>
      </div>
      <div class="app-card-body">
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field v-model="filtro.data_inicial" label="Data inicial" type="datetime-local" />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field v-model="filtro.data_final" label="Data final" type="datetime-local" />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field v-model="filtro.cliente" label="Cliente" />
          </v-col>
          <v-col cols="12" md="3">
            <v-select :items="tiposSaida" v-model="filtro.tipo_saida" label="Tipo saída" clearable />
          </v-col>
        </v-row>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <StatCard label="Total vendido" :value="formatBRL(resumo?.total_vendido)" icon="mdi-cash" variant="primary" />
      <StatCard label="Total custo" :value="formatBRL(resumo?.total_custo)" icon="mdi-receipt-text-outline" variant="info" />
      <StatCard label="Total lucro" :value="formatBRL(resumo?.total_lucro)" icon="mdi-finance" variant="success" />
      <StatCard label="Qtd. vendas" :value="String(resumo?.quantidade_vendas ?? 0)" icon="mdi-cart-outline" variant="accent" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="app-card overflow-hidden">
        <div class="app-card-header">
          <div>
            <div class="app-card-title">Por cliente</div>
            <div class="app-card-subtitle">Resumo agregado por cliente</div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th class="text-right">Qtd vendas</th>
                <th class="text-right">Total</th>
                <th class="text-right">Lucro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in porCliente" :key="it.cliente_nome">
                <td class="font-medium">{{ it.cliente_nome }}</td>
                <td class="text-right text-muted-foreground">{{ it.quantidade_vendas }}</td>
                <td class="text-right font-medium">{{ formatBRL(it.total_vendido) }}</td>
                <td class="text-right font-medium text-success">{{ formatBRL(it.total_lucro) }}</td>
              </tr>
              <tr v-if="!porCliente.length">
                <td colspan="4">
                  <EmptyState icon="mdi-account" title="Sem dados" description="Gere o relatório para ver os resultados por cliente." />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="app-card overflow-hidden">
        <div class="app-card-header">
          <div>
            <div class="app-card-title">Por marca</div>
            <div class="app-card-subtitle">Resumo agregado por marca</div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th>Marca</th>
                <th class="text-right">Qtd itens</th>
                <th class="text-right">Qtd total</th>
                <th class="text-right">Total</th>
                <th class="text-right">Lucro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in porMarca" :key="it.produto__marca">
                <td class="font-medium">{{ it.produto__marca }}</td>
                <td class="text-right text-muted-foreground">{{ it.quantidade_itens }}</td>
                <td class="text-right text-muted-foreground">{{ it.quantidade_total }}</td>
                <td class="text-right font-medium">{{ formatBRL(it.total_vendido) }}</td>
                <td class="text-right font-medium text-success">{{ formatBRL(it.total_lucro) }}</td>
              </tr>
              <tr v-if="!porMarca.length">
                <td colspan="5">
                  <EmptyState icon="mdi-factory" title="Sem dados" description="Gere o relatório para ver os resultados por marca." />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api/client'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL } from '@/lib/formatters'

const tiposSaida = [
  { title: 'Retirada', value: 'RETIRADA' },
  { title: 'Entrega', value: 'ENTREGA' },
]

const filtro = ref<any>({
  data_inicial: '',
  data_final: '',
  cliente: '',
  tipo_saida: null,
})

const resumo = ref<any>(null)
const porCliente = ref<any[]>([])
const porMarca = ref<any[]>([])
const loading = ref(false)

function buildParams() {
  const params = new URLSearchParams()
  if (filtro.value.data_inicial) params.set('data_inicial', new Date(filtro.value.data_inicial).toISOString())
  if (filtro.value.data_final) params.set('data_final', new Date(filtro.value.data_final).toISOString())
  if (filtro.value.cliente) params.set('cliente', filtro.value.cliente)
  if (filtro.value.tipo_saida) params.set('tipo_saida', filtro.value.tipo_saida)
  return params
}

async function load() {
  loading.value = true
  const params = buildParams()
  try {
    const [r1, r2, r3] = await Promise.all([
      api.get(`/relatorios/resumo/?${params.toString()}`),
      api.get(`/relatorios/por-cliente/?${params.toString()}`),
      api.get(`/relatorios/por-marca/?${params.toString()}`),
    ])
    resumo.value = r1.data
    porCliente.value = r2.data
    porMarca.value = r3.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
