<template>
  <div class="min-h-screen bg-background text-foreground">
    <div class="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
      <section class="relative hidden overflow-hidden bg-sidebar lg:flex">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.08),_transparent_35%),linear-gradient(135deg,_rgba(255,255,255,0.04),_transparent_45%)]" />
        <div class="absolute -left-20 top-20 h-64 w-64 rounded-full bg-primary/20 blur-3xl" />
        <div class="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-accent/10 blur-3xl" />

        <div class="relative z-10 flex w-full flex-col justify-between p-10 xl:p-14">
          <div class="flex items-center gap-4">
            <div class="flex h-14 w-14 items-center justify-center rounded-[calc(var(--radius)+0.25rem)] bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <span class="mdi mdi-text-box-check-outline text-3xl" />
            </div>
            <div>
              <div class="text-2xl font-bold tracking-tight text-sidebar-foreground">Batatã</div>
              <p class="text-sm text-sidebar-foreground/65">Gestão interna de estoque e vendas de cimento</p>
            </div>
          </div>

          <div class="max-w-xl space-y-8">
            <div class="space-y-4">
              <span class="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.22em] text-sidebar-foreground/70">
                Controle operacional
              </span>
              <h1 class="text-4xl font-semibold leading-tight text-sidebar-foreground xl:text-5xl">
                Estoque, entradas e vendas em um único painel.
              </h1>
              <p class="max-w-lg text-base leading-7 text-sidebar-foreground/70 xl:text-lg">
                Organize produtos, acompanhe movimentações e visualize lucro com uma interface simples,
                rápida e pensada para a rotina da loja.
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="rounded-[var(--radius)] border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary">
                  <span class="mdi mdi-chart-line text-2xl" />
                </div>
                <h2 class="text-sm font-semibold text-sidebar-foreground">Visão rápida do negócio</h2>
                <p class="mt-2 text-sm leading-6 text-sidebar-foreground/65">
                  Acompanhe vendas, margem de lucro e produtos com estoque baixo no mesmo sistema.
                </p>
              </div>

              <div class="rounded-[var(--radius)] border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-accent/15 text-accent">
                  <span class="mdi mdi-swap-horizontal text-2xl" />
                </div>
                <h2 class="text-sm font-semibold text-sidebar-foreground">Fluxo de loja</h2>
                <p class="mt-2 text-sm leading-6 text-sidebar-foreground/65">
                  Registre entradas e vendas com atualização automática do estoque e custo médio.
                </p>
              </div>
            </div>
          </div>

          <div class="text-sm text-sidebar-foreground/50">
            Sistema interno para operação local e uso offline no Windows.
          </div>
        </div>
      </section>

      <section class="relative flex items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(59,130,246,0.10),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(245,158,11,0.10),_transparent_26%)]" />

        <div class="relative z-10 w-full max-w-md">
          <div class="mb-8 flex items-center gap-4 lg:hidden">
            <div class="flex h-12 w-12 items-center justify-center rounded-[var(--radius)] bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <span class="mdi mdi-text-box-check-outline text-2xl" />
            </div>
            <div>
              <div class="text-lg font-bold">Batatã</div>
              <p class="text-sm text-muted-foreground">Gestão de estoque e vendas</p>
            </div>
          </div>

          <div class="rounded-[calc(var(--radius)+0.5rem)] border border-border/70 bg-card/90 p-7 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.35)] backdrop-blur sm:p-8">
            <div class="mb-8 space-y-2">
              <span class="inline-flex rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                Acesso ao sistema
              </span>
              <h2 class="text-3xl font-semibold tracking-tight">Entrar na sua conta</h2>
              <p class="text-sm leading-6 text-muted-foreground">
                Acesse o painel de controle do estoque de cimento com seu usuário e senha.
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
                    class="h-13 w-full rounded-[var(--radius)] border border-border bg-background pl-12 pr-4 text-[15px] text-foreground outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
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
                    class="h-13 w-full rounded-[var(--radius)] border border-border bg-background pl-12 pr-4 text-[15px] text-foreground outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10"
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
                class="inline-flex h-13 w-full items-center justify-center gap-2 rounded-[var(--radius)] bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
                :disabled="auth.loading"
              >
                <span v-if="auth.loading" class="h-5 w-5 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                <span>{{ auth.loading ? 'Entrando...' : 'Entrar no sistema' }}</span>
              </button>
            </form>

            <div class="mt-6 rounded-[var(--radius)] bg-muted/70 px-4 py-3 text-sm leading-6 text-muted-foreground">
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
