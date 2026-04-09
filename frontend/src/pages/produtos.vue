<template>
  <div class="max-w-7xl mx-auto">
    <PageHeader title="Materiais" description="Cadastro e manutenção do catálogo da loja">
      <template #actions>
        <AppButton icon="mdi-plus" @click="openCreate">Novo material</AppButton>
        <AppButton variant="outline" icon="mdi-refresh" @click="load">Atualizar</AppButton>
      </template>
    </PageHeader>

    <div class="app-card overflow-hidden">
      <div class="app-card-header">
        <div>
          <div class="app-card-title">Lista de materiais</div>
          <div class="app-card-subtitle">Gerencie categoria, unidade, preços e status</div>
        </div>
      </div>

      <AppSpinner v-if="loading" />

      <div v-else class="overflow-x-auto">
        <table class="app-table">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Marca</th>
              <th>Nome</th>
              <th class="text-right">Medida</th>
              <th class="text-right">Custo</th>
              <th class="text-right">Preço</th>
              <th class="text-right">Lucro</th>
              <th>Status</th>
              <th class="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="text-muted-foreground">{{ item.tipo_material_label }}</td>
              <td class="text-muted-foreground">{{ item.marca_label || '-' }}</td>
              <td class="font-medium">{{ item.nome_produto }}</td>
              <td class="text-right">{{ formatMaterialMeasure(item) }}</td>
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
              <td colspan="9">
                <EmptyState
                  icon="mdi-cube-outline"
                  title="Sem materiais cadastrados"
                  description="Clique em 'Novo material' para cadastrar o primeiro item do catálogo."
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal
      v-model="dialogOpen"
      :title="form.id ? 'Editar material' : 'Novo material'"
      description="Defina categoria, unidade, conversões e precificação do item"
      max-width="xl"
    >
      <form class="space-y-6" @submit.prevent="save">
        <div class="grid gap-4 md:grid-cols-12">
          <div class="md:col-span-3">
            <AppSelect v-model="form.tipo_material" :items="tipoMaterialOptions" label="Tipo do material" />
          </div>
          <div class="md:col-span-4">
            <AppInput v-model="form.nome_produto" label="Nome" placeholder="Ex: CP-II 50kg ou Tijolo 8 furos" />
          </div>
          <div class="md:col-span-5">
            <AppInput v-model="form.descricao_produto" label="Descrição" placeholder="Observações internas do produto" />
          </div>

          <div v-if="isCimento" class="md:col-span-3">
            <AppSelect v-model="form.marca" :items="marcasCimento" label="Marca do cimento" />
          </div>
          <div v-else class="md:col-span-3">
            <div class="rounded-(--radius) border border-dashed border-border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
              Materiais não cimentícios não exigem marca fixa.
            </div>
          </div>

          <div class="md:col-span-3">
            <AppSelect v-model="form.unidade_estoque" :items="unitOptions" label="Unidade de estoque" />
          </div>
          <div class="md:col-span-3">
            <AppSelect v-model="form.unidade_medida" :items="unitOptions" label="Unidade comercial" />
          </div>
          <div class="md:col-span-3">
            <AppInput
              v-model="form.quantidade_por_unidade"
              :label="measureFieldLabel"
              type="number"
              min="0"
              step="0.001"
            />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="form.custo_unitario_fabrica" label="Custo base" type="number" min="0" step="0.01" />
          </div>
          <div class="md:col-span-3">
            <AppInput v-model="form.preco_unitario_loja" label="Preço de venda" type="number" min="0" step="0.01" />
          </div>
          <div class="md:col-span-6 flex items-end">
            <label class="flex h-11 w-full items-center justify-between rounded-(--radius) border border-border bg-background px-4">
              <span class="text-sm font-medium text-foreground">Material ativo</span>
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

        <div class="grid gap-6 lg:grid-cols-2">
          <div class="rounded-(--radius) border border-border bg-background p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-foreground">Conversões de unidade</div>
                <div class="text-sm text-muted-foreground">Use para areia por carrada e lata, ou outras formas de venda.</div>
              </div>
              <AppButton variant="outline" icon="mdi-plus" @click="addConversion">Adicionar</AppButton>
            </div>

            <div v-if="!form.conversoes_unidade.length" class="rounded-(--radius) border border-dashed border-border px-4 py-3 text-sm text-muted-foreground">
              Nenhuma conversão cadastrada.
            </div>

            <div v-for="(row, index) in form.conversoes_unidade" :key="`conv-${index}`" class="mb-3 grid gap-3 md:grid-cols-12">
              <div class="md:col-span-4">
                <AppSelect v-model="row.unidade_origem" :items="unitOptions" label="Origem" />
              </div>
              <div class="md:col-span-4">
                <AppSelect v-model="row.unidade_destino" :items="unitOptions" label="Destino" />
              </div>
              <div class="md:col-span-3">
                <AppInput v-model="row.fator_multiplicador" label="Fator" type="number" min="0.000001" step="0.000001" />
              </div>
              <div class="md:col-span-1 flex items-end justify-end">
                <AppButton variant="ghost" icon="mdi-delete-outline" @click="removeConversion(Number(index))" />
              </div>
            </div>
          </div>

          <div class="rounded-(--radius) border border-border bg-background p-4">
            <div class="mb-4 flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-foreground">Preços por unidade</div>
                <div class="text-sm text-muted-foreground">Cadastre preço por lata, carrada, milheiro ou qualquer outra unidade de venda.</div>
              </div>
              <AppButton variant="outline" icon="mdi-plus" @click="addPrice">Adicionar</AppButton>
            </div>

            <div v-if="!form.precos_venda.length" class="rounded-(--radius) border border-dashed border-border px-4 py-3 text-sm text-muted-foreground">
              Sem preços extras. O preço base vale para a unidade comercial/estoque.
            </div>

            <div v-for="(row, index) in form.precos_venda" :key="`price-${index}`" class="mb-3 grid gap-3 md:grid-cols-12">
              <div class="md:col-span-6">
                <AppSelect v-model="row.unidade_venda" :items="unitOptions" label="Unidade de venda" />
              </div>
              <div class="md:col-span-5">
                <AppInput v-model="row.preco_unitario" label="Preço" type="number" min="0" step="0.01" />
              </div>
              <div class="md:col-span-1 flex items-end justify-end">
                <AppButton variant="ghost" icon="mdi-delete-outline" @click="removePrice(Number(index))" />
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-(--radius) border border-border bg-muted/35 px-4 py-3 text-sm text-muted-foreground">
          A unidade de estoque define como o saldo será controlado. Para areia, use metro e cadastre conversões como carrada e lata.
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
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatBRL, formatMaterialMeasure, getUnitLabel } from '@/lib/formatters'

const tipoMaterialOptions = [
  { title: 'Cimento', value: 'CIMENTO' },
  { title: 'Tijolo', value: 'TIJOLO' },
  { title: 'Areia', value: 'AREIA' },
  { title: 'Outros', value: 'OUTRO' },
]

const marcasCimento = [
  { title: 'Itaqui', value: 'ITAQUI' },
  { title: 'Bravo', value: 'BRAVO' },
  { title: 'Poty', value: 'POTY' },
  { title: 'Monte Carlos', value: 'MONTE_CARLOS' },
]

const unitOptions = [
  { title: 'Kg', value: 'KG' },
  { title: 'Unidade', value: 'UNIDADE' },
  { title: 'Lata', value: 'LATA' },
  { title: 'Milheiro', value: 'MILHEIRO' },
  { title: 'Carrada', value: 'CARRADA' },
  { title: 'Metro', value: 'METRO' },
  { title: 'Metro quadrado', value: 'METRO_QUADRADO' },
  { title: 'Metro cúbico', value: 'METRO_CUBICO' },
  { title: 'Pacote', value: 'PACOTE' },
]

const items = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogOpen = ref(false)
const form = ref<any>({})
const hydratingForm = ref(false)

const isCimento = computed(() => form.value.tipo_material === 'CIMENTO')
const measureFieldLabel = computed(() => {
  switch (form.value.unidade_estoque) {
    case 'KG':
      return 'Peso por item (kg)'
    case 'UNIDADE':
      return 'Quantidade por item'
    default:
      return 'Medida por item'
  }
})

function getQuantidadeStep() {
  return form.value.unidade_estoque === 'UNIDADE' ? '1' : '0.001'
}

function createConversionRow(data: Record<string, any> = {}) {
  return {
    unidade_origem: data.unidade_origem ?? null,
    unidade_destino: data.unidade_destino ?? form.value.unidade_estoque ?? null,
    fator_multiplicador: data.fator_multiplicador ?? '',
    ativo: data.ativo ?? true,
  }
}

function createPriceRow(data: Record<string, any> = {}) {
  return {
    unidade_venda: data.unidade_venda ?? null,
    preco_unitario: data.preco_unitario ?? '',
    ativo: data.ativo ?? true,
  }
}

function getPresetByType(tipoMaterial: string) {
  switch (tipoMaterial) {
    case 'CIMENTO':
      return {
        marca: 'ITAQUI',
        unidade_estoque: 'KG',
        unidade_medida: 'KG',
        quantidade_por_unidade: 50,
        conversoes_unidade: [],
        precos_venda: [],
      }
    case 'AREIA':
      return {
        marca: '',
        unidade_estoque: 'METRO',
        unidade_medida: 'METRO',
        quantidade_por_unidade: 1,
        conversoes_unidade: [
          createConversionRow({ unidade_origem: 'CARRADA', unidade_destino: 'METRO', fator_multiplicador: 6 }),
          createConversionRow({ unidade_origem: 'METRO', unidade_destino: 'LATA', fator_multiplicador: 50 }),
        ],
        precos_venda: [createPriceRow({ unidade_venda: 'LATA', preco_unitario: 3 })],
      }
    case 'TIJOLO':
      return {
        marca: '',
        unidade_estoque: 'UNIDADE',
        unidade_medida: 'UNIDADE',
        quantidade_por_unidade: 1,
        conversoes_unidade: [createConversionRow({ unidade_origem: 'MILHEIRO', unidade_destino: 'UNIDADE', fator_multiplicador: 1000 })],
        precos_venda: [],
      }
    default:
      return {
        marca: '',
        unidade_estoque: 'UNIDADE',
        unidade_medida: 'UNIDADE',
        quantidade_por_unidade: 1,
        conversoes_unidade: [],
        precos_venda: [],
      }
  }
}

function createDefaultForm() {
  const preset = getPresetByType('CIMENTO')
  return {
    id: null,
    tipo_material: 'CIMENTO',
    marca: preset.marca,
    nome_produto: '',
    descricao_produto: '',
    unidade_estoque: preset.unidade_estoque,
    unidade_medida: preset.unidade_medida,
    quantidade_por_unidade: preset.quantidade_por_unidade,
    custo_unitario_fabrica: 0,
    preco_unitario_loja: 0,
    conversoes_unidade: preset.conversoes_unidade,
    precos_venda: preset.precos_venda,
    ativo: true,
  }
}

function normalizePayload() {
  return {
    ...form.value,
    marca: form.value.tipo_material === 'CIMENTO' ? form.value.marca : '',
    unidade_estoque: String(form.value.unidade_estoque ?? 'UNIDADE'),
    unidade_medida: String(form.value.unidade_medida ?? form.value.unidade_estoque ?? 'UNIDADE'),
    quantidade_por_unidade: Number(form.value.quantidade_por_unidade ?? 0),
    custo_unitario_fabrica: Number(form.value.custo_unitario_fabrica ?? 0),
    preco_unitario_loja: Number(form.value.preco_unitario_loja ?? 0),
    conversoes_unidade: (form.value.conversoes_unidade ?? [])
      .filter((item: any) => item.unidade_origem && item.unidade_destino && Number(item.fator_multiplicador) > 0)
      .map((item: any) => ({
        unidade_origem: String(item.unidade_origem),
        unidade_destino: String(item.unidade_destino),
        fator_multiplicador: String(item.fator_multiplicador),
        ativo: item.ativo !== false,
      })),
    precos_venda: (form.value.precos_venda ?? [])
      .filter((item: any) => item.unidade_venda && item.preco_unitario !== '' && item.preco_unitario != null)
      .map((item: any) => ({
        unidade_venda: String(item.unidade_venda),
        preco_unitario: String(item.preco_unitario),
        ativo: item.ativo !== false,
      })),
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function fetchItems() {
  const { data } = await api.get('/produtos/?ordering=tipo_material,nome_produto')
  items.value = data
}

function reset() {
  form.value = createDefaultForm()
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
  hydratingForm.value = true
  form.value = {
    ...item,
    marca: item.marca ?? '',
    unidade_estoque: item.unidade_estoque ?? item.unidade_medida ?? 'UNIDADE',
    unidade_medida: item.unidade_medida ?? item.unidade_estoque ?? 'UNIDADE',
    quantidade_por_unidade: Number(item.quantidade_por_unidade ?? 1),
    custo_unitario_fabrica: Number(item.custo_unitario_fabrica ?? 0),
    preco_unitario_loja: Number(item.preco_unitario_loja ?? 0),
    conversoes_unidade: (item.conversoes_unidade ?? []).map((row: any) => createConversionRow(row)),
    precos_venda: (item.precos_venda ?? []).map((row: any) => createPriceRow(row)),
  }
  hydratingForm.value = false
  dialogOpen.value = true
}

function closeDialog() {
  dialogOpen.value = false
  reset()
}

function addConversion() {
  form.value.conversoes_unidade.push(createConversionRow())
}

function removeConversion(index: number) {
  form.value.conversoes_unidade.splice(index, 1)
}

function addPrice() {
  form.value.precos_venda.push(createPriceRow({ unidade_venda: form.value.unidade_estoque }))
}

function removePrice(index: number) {
  form.value.precos_venda.splice(index, 1)
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
  if (!confirm('Excluir este material? Pode falhar se já houver entradas ou vendas.')) return
  await api.delete(`/produtos/${item.id}/`)
  await load(2000)
}

watch(
  () => form.value.tipo_material,
  (tipoAtual, tipoAnterior) => {
    if (hydratingForm.value) return

    const preset = getPresetByType(String(tipoAtual ?? 'OUTRO'))
    if (tipoAtual === 'CIMENTO') {
      if (!form.value.marca) form.value.marca = 'ITAQUI'
      if (!form.value.id || tipoAnterior !== 'CIMENTO') {
        form.value.unidade_estoque = preset.unidade_estoque
        form.value.unidade_medida = preset.unidade_medida
        form.value.quantidade_por_unidade = preset.quantidade_por_unidade
        form.value.conversoes_unidade = preset.conversoes_unidade
        form.value.precos_venda = preset.precos_venda
      }
      return
    }

    form.value.marca = ''
    if (!form.value.id || tipoAnterior === 'CIMENTO') {
      form.value.unidade_estoque = preset.unidade_estoque
      form.value.unidade_medida = preset.unidade_medida
      form.value.quantidade_por_unidade = preset.quantidade_por_unidade
      form.value.conversoes_unidade = preset.conversoes_unidade
      form.value.precos_venda = preset.precos_venda
    }
  },
)

watch(
  () => form.value.unidade_estoque,
  (unidadeAtual) => {
    if (!unidadeAtual) return
    for (const row of form.value.conversoes_unidade ?? []) {
      if (!row.unidade_destino) row.unidade_destino = unidadeAtual
    }
  },
)

onMounted(() => {
  reset()
  load()
})
</script>
