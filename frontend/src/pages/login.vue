<template>
  <div class="min-h-screen bg-[linear-gradient(135deg,_#eef5e8_0%,_#fffbea_42%,_#ece1cf_100%)] text-foreground">
    <div class="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
      <section class="relative hidden overflow-hidden bg-[linear-gradient(160deg,_#234833_0%,_#3a6b45_36%,_#8d6233_100%)] lg:flex">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,250,230,0.18),_transparent_32%),linear-gradient(135deg,_rgba(255,255,255,0.04),_transparent_48%)]" />
        <div class="absolute -left-20 top-20 h-64 w-64 rounded-full bg-[#f0ce63]/20 blur-3xl" />
        <div class="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-[#9cc16b]/18 blur-3xl" />
        <div class="absolute inset-y-0 right-0 w-px bg-white/10" />

        <div class="relative z-10 flex w-full flex-col justify-between p-10 xl:p-14">
          <div class="flex items-center gap-5 xl:gap-6">
            <div class="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-[calc(var(--radius)+0.45rem)] border border-white/15 bg-white/95 p-2 shadow-lg shadow-black/20 backdrop-blur-sm xl:h-28 xl:w-28">
              <img src="/batatalogo.jpeg" alt="Logo Material de Construção Batatã" class="h-full w-full object-contain" />
            </div>
            <div class="min-w-0 max-w-[28rem] space-y-1">
              <div class="text-[2rem] font-bold leading-tight tracking-tight text-white xl:text-[2.25rem]">
                Material de Construção Batatã
              </div>
              <p class="text-sm text-white/72 xl:text-base">Gestão interna de estoque, vendas e orçamentos</p>
            </div>
          </div>

          <div class="max-w-xl space-y-8">
            <div class="space-y-4">
              <span class="inline-flex rounded-full border border-white/15 bg-white/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.22em] text-[#fff0b3]">
                Controle operacional
              </span>
              <h1 class="text-4xl font-semibold leading-tight text-white xl:text-5xl">
                Estoque, entradas e vendas em um único painel.
              </h1>
              <p class="max-w-lg text-base leading-7 text-white/72 xl:text-lg">
                Organize produtos, acompanhe movimentações e visualize lucro com uma interface simples,
                rápida e pensada para a rotina da loja.
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="rounded-[var(--radius)] border border-white/12 bg-white/8 p-5 backdrop-blur-sm">
                <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#f0ce63]/18 text-[#ffea9d]">
                  <span class="mdi mdi-chart-line text-2xl" />
                </div>
                <h2 class="text-sm font-semibold text-white">Visão rápida do negócio</h2>
                <p class="mt-2 text-sm leading-6 text-white/68">
                  Acompanhe vendas, margem de lucro e produtos com estoque baixo no mesmo sistema.
                </p>
              </div>

              <div class="rounded-[var(--radius)] border border-white/12 bg-white/8 p-5 backdrop-blur-sm">
                <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#c3df9d]/16 text-[#f4f1b8]">
                  <span class="mdi mdi-swap-horizontal text-2xl" />
                </div>
                <h2 class="text-sm font-semibold text-white">Fluxo de loja</h2>
                <p class="mt-2 text-sm leading-6 text-white/68">
                  Registre entradas e vendas com atualização automática do estoque e custo médio.
                </p>
              </div>
            </div>
          </div>

          <div class="text-sm text-white/52">
            Sistema interno para operação local e uso offline no Windows.
          </div>
        </div>
      </section>

      <section class="relative flex items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(103,152,87,0.16),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(228,194,80,0.14),_transparent_26%)]" />
        <div class="absolute inset-y-0 left-0 hidden w-24 bg-[linear-gradient(180deg,_rgba(58,107,69,0.08),_rgba(141,98,51,0))] lg:block" />

        <div class="relative z-10 w-full max-w-md">
          <div class="mb-8 flex items-center gap-4 lg:hidden">
            <div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-[var(--radius)] border border-[#d7d7c8] bg-white p-1.5 shadow-lg shadow-[#3a6b45]/10">
              <img src="/batatalogo.jpeg" alt="Logo Material de Construção Batatã" class="h-full w-full object-contain" />
            </div>
            <div class="min-w-0">
              <div class="text-lg font-bold leading-tight text-[#2f5a39]">Material de Construção Batatã</div>
              <p class="text-sm text-muted-foreground">Gestão de estoque, vendas e orçamentos</p>
            </div>
          </div>

          <div class="rounded-[calc(var(--radius)+0.5rem)] border border-[#d4ddc9]/90 bg-white/88 p-7 shadow-[0_28px_80px_-32px_rgba(58,107,69,0.22)] backdrop-blur sm:p-8">
            <div class="mb-8 space-y-2">
              <span class="inline-flex rounded-full bg-[#3a6b45]/10 px-3 py-1 text-xs font-semibold text-[#3a6b45]">
                Acesso ao sistema
              </span>
              <h2 class="text-3xl font-semibold tracking-tight text-[#233625]">Entrar na sua conta</h2>
              <p class="text-sm leading-6 text-muted-foreground">
                Acesse o painel de controle dos materiais de construção com seu usuário e senha.
              </p>
            </div>

            <form class="space-y-5" @submit.prevent="onSubmit">
              <div class="space-y-2">
                <label for="username" class="text-sm font-medium text-foreground">Usuário</label>
                <div class="relative">
                  <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-muted-foreground">
                    <span class="mdi mdi-account-outline text-xl" />
                  </span>
                  <input
                    id="username"
                    v-model="username"
                    type="text"
                    autocomplete="username"
                    placeholder="Digite seu usuário"
                    class="h-13 w-full rounded-[var(--radius)] border border-[#d6deca] bg-[#fbfdf8] pl-12 pr-4 text-[15px] text-foreground outline-none transition focus:border-[#3a6b45] focus:ring-4 focus:ring-[#3a6b45]/10"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <label for="password" class="text-sm font-medium text-foreground">Senha</label>
                <div class="relative">
                  <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-muted-foreground">
                    <span class="mdi mdi-lock-outline text-xl" />
                  </span>
                  <input
                    id="password"
                    v-model="password"
                    type="password"
                    autocomplete="current-password"
                    placeholder="Digite sua senha"
                    class="h-13 w-full rounded-[var(--radius)] border border-[#d6deca] bg-[#fbfdf8] pl-12 pr-4 text-[15px] text-foreground outline-none transition focus:border-[#3a6b45] focus:ring-4 focus:ring-[#3a6b45]/10"
                  />
                </div>
              </div>

              <div
                v-if="error"
                class="rounded-[var(--radius)] border border-error/20 bg-error/8 px-4 py-3 text-sm leading-6 text-error"
              >
                {{ error }}
              </div>

              <button
                type="submit"
                class="inline-flex h-13 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-[linear-gradient(135deg,_#3a6b45_0%,_#6d8a33_55%,_#8d6233_100%)] px-4 text-sm font-semibold text-white shadow-lg shadow-[#3a6b45]/20 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
                :disabled="auth.loading"
              >
                <span v-if="auth.loading" class="h-5 w-5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                <span>{{ auth.loading ? 'Entrando...' : 'Entrar no sistema' }}</span>
              </button>
            </form>

            <div class="mt-6 rounded-[var(--radius)] border border-[#e2e5d7] bg-[#f7f8ef] px-4 py-3 text-sm leading-6 text-muted-foreground">
              Dica: se for o primeiro acesso, crie um usuário pelo admin do Django ou use o usuário demo configurado.
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')

async function onSubmit() {
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    await auth.fetchMe()
    await router.replace('/dashboard')
  } catch (e: any) {
    const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'
    error.value =
      e?.response?.data?.non_field_errors?.[0] ??
      (typeof e?.response?.data === 'string' ? e.response.data : null) ??
      (e?.response?.data ? JSON.stringify(e.response.data) : null) ??
      `Não foi possível conectar ao backend (${apiBase}). Verifique se o Django está rodando.`
  }
}
</script>
