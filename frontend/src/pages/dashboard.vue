<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Dashboard" description="Visão geral de estoque, vendas e lucro">
      <template #actions>
        <AppButton variant="outline" icon="mdi-refresh" @click="load" :loading="loading">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div v-if="loading" class="mb-6">
      <AppSpinner :centered="false" />
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <StatCard
        label="Qtd. em estoque"
        :value="String(dashboard?.quantidade_total_estoque ?? 0)"
        icon="mdi-warehouse"
        variant="info"
      />
      <StatCard label="Investido" :value="formatBRL(dashboard?.valor_total_investido_estoque)" icon="mdi-cash" variant="accent" />
      <StatCard
        label="Potencial de venda"
        :value="formatBRL(dashboard?.valor_total_potencial_venda)"
        icon="mdi-trending-up"
        variant="primary"
      />
      <StatCard
        label="Lucro potencial"
        :value="formatBRL(dashboard?.lucro_potencial_estoque)"
        icon="mdi-finance"
        variant="success"
      />
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <div class="app-card p-6">
        <p class="text-sm text-muted-foreground">Vendido hoje</p>
        <p class="text-xl font-bold text-foreground mt-1">{{ formatBRL(dashboard?.total_vendido_dia) }}</p>
      </div>
      <div class="app-card p-6">
        <p class="text-sm text-muted-foreground">Vendido no mês</p>
        <p class="text-xl font-bold text-foreground mt-1">{{ formatBRL(dashboard?.total_vendido_mes) }}</p>
      </div>
      <div class="app-card p-6">
        <p class="text-sm text-muted-foreground">Lucro hoje</p>
        <p class="text-xl font-bold text-foreground mt-1">{{ formatBRL(dashboard?.lucro_dia) }}</p>
      </div>
      <div class="app-card p-6">
        <p class="text-sm text-muted-foreground">Lucro no mês</p>
        <p class="text-xl font-bold text-foreground mt-1">{{ formatBRL(dashboard?.lucro_mes) }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="app-card overflow-hidden lg:col-span-2">
        <div class="app-card-header">
          <div>
            <div class="app-card-title">Últimas vendas</div>
            <div class="app-card-subtitle">Movimentações recentes de saída</div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Cliente</th>
                <th>Tipo</th>
                <th class="text-right">Total</th>
                <th class="text-right">Lucro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in ultimasVendas" :key="v.id">
                <td class="text-muted-foreground">{{ formatDateTime(v.data_venda) }}</td>
                <td class="font-medium">{{ v.cliente_nome }}</td>
                <td>
                  <span
                    class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                    :class="v.tipo_saida === 'ENTREGA' ? 'bg-accent/10 text-accent' : 'bg-primary/10 text-primary'"
                  >
                    {{ v.tipo_saida }}
                  </span>
                </td>
                <td class="text-right font-medium">{{ formatBRL(v.valor_total_venda) }}</td>
                <td class="text-right font-medium text-success">{{ formatBRL(v.lucro_total_venda) }}</td>
              </tr>
              <tr v-if="!ultimasVendas.length">
                <td colspan="5">
                  <EmptyState icon="mdi-cart-outline" title="Sem vendas" description="Quando você registrar vendas, elas aparecem aqui." />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="app-card overflow-hidden">
        <div class="app-card-header">
          <div>
            <div class="app-card-title">Estoque baixo</div>
            <div class="app-card-subtitle">Atenção para reposição</div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th>Material</th>
                <th>Tipo</th>
                <th class="text-right">Qtd</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in estoqueBaixo" :key="e.produto?.id ?? e.id">
                <td class="font-medium">{{ formatMaterialLabel(e.produto) }}</td>
                <td class="text-muted-foreground">{{ e.produto?.tipo_material_label }}</td>
                <td class="text-right font-medium">{{ e.quantidade_atual }}</td>
              </tr>
              <tr v-if="!estoqueBaixo.length">
                <td colspan="3">
                  <EmptyState icon="mdi-warehouse" title="Tudo certo" description="Nenhum material está com estoque baixo." />
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
import { computed, onMounted, ref } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL, formatDateTime, formatMaterialLabel } from '@/lib/formatters'

const dashboard = ref<any>(null)
const loading = ref(false)

const ultimasVendas = computed<any[]>(() => dashboard.value?.ultimas_vendas ?? [])
const estoqueBaixo = computed<any[]>(() => dashboard.value?.produtos_estoque_baixo ?? [])

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/dashboard/')
    dashboard.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
