<template>
  <v-app>
    <template v-if="showShell">
      <button
        type="button"
        class="lg:hidden fixed top-4 left-4 z-50 h-10 w-10 rounded-(--radius) bg-card shadow-sm flex items-center justify-center"
        aria-label="Abrir menu"
        @click="mobileOpen = true"
      >
        <span class="mdi mdi-menu text-xl text-foreground" />
      </button>

      <div
        v-if="mobileOpen && !lgAndUp"
        class="fixed inset-0 z-40 bg-black/50"
        @click="mobileOpen = false"
      />

      <aside
        class="fixed inset-y-0 left-0 z-50 w-64 bg-sidebar text-sidebar-foreground transform transition-transform duration-300 lg:translate-x-0"
        :class="{
          '-translate-x-full': !mobileOpen && !lgAndUp,
          'translate-x-0': mobileOpen || lgAndUp,
        }"
      >
        <div class="p-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-(--radius) bg-primary flex items-center justify-center">
              <span class="mdi mdi-text-box-check-outline text-xl text-primary-foreground" />
            </div>
            <div>
              <h1 class="text-lg font-bold">Batatã</h1>
              <p class="text-sm text-sidebar-foreground/60">Gestão de Materiais</p>
            </div>
          </div>
        </div>

        <nav class="px-4 space-y-2">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-3 px-4 py-3 rounded-(--radius) transition-colors"
            :class="
              isActive(item.to)
                ? 'bg-primary text-primary-foreground'
                : 'text-sidebar-foreground/80 hover:bg-sidebar-muted hover:text-sidebar-foreground'
            "
            @click="onNavClick"
          >
            <span :class="['mdi', item.icon, 'text-xl']" />
            <span class="font-medium">{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="absolute bottom-0 left-0 right-0 p-4">
          <div v-if="auth.user?.username" class="mb-3 text-xs text-sidebar-foreground/60 px-2">
            Logado como: <span class="font-medium text-sidebar-foreground/80">{{ auth.user?.username }}</span>
          </div>
          <button
            type="button"
            class="w-full flex items-center gap-3 px-4 py-3 rounded-(--radius) text-sidebar-foreground/80 hover:bg-sidebar-muted hover:text-sidebar-foreground transition-colors"
            @click="onLogout"
          >
            <span class="mdi mdi-logout text-xl" />
            <span class="font-medium">Sair do Sistema</span>
          </button>
        </div>
      </aside>

      <main class="min-h-screen bg-background lg:ml-64">
        <div class="p-4 pt-16 lg:p-8 lg:pt-8">
          <router-view />
        </div>
      </main>
    </template>

    <template v-else>
      <router-view />
    </template>
  </v-app>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDisplay } from 'vuetify'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const display = useDisplay()

const mobileOpen = ref(false)

const lgAndUp = computed(() => display.lgAndUp.value)

const showShell = computed(() => auth.isAuthenticated && route.path !== '/login')

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'mdi-view-dashboard-outline' },
  { to: '/produtos', label: 'Materiais', icon: 'mdi-cube-outline' },
  { to: '/entradas', label: 'Entradas', icon: 'mdi-tray-arrow-down' },
  { to: '/vendas', label: 'Vendas', icon: 'mdi-cart-outline' },
  { to: '/orcamentos', label: 'Orçamentos', icon: 'mdi-file-document-outline' },
  { to: '/movimentacoes', label: 'Movimentações', icon: 'mdi-swap-horizontal' },
  { to: '/relatorios', label: 'Relatórios', icon: 'mdi-chart-line' },
]

function isActive(to: string) {
  return route.path === to
}

function onNavClick() {
  if (!lgAndUp.value) mobileOpen.value = false
}

watch(
  () => route.path,
  () => {
    if (!lgAndUp.value) mobileOpen.value = false
  },
)

watch(lgAndUp, (isDesktop) => {
  if (isDesktop) mobileOpen.value = false
})

async function onLogout() {
  await auth.logout()
  await router.replace('/login')
}
</script>
