/**
 * router/index.ts
 *
 * Manual routes for ./src/pages/*.vue
 */

// Composables
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import Login from '@/pages/login.vue'
import Dashboard from '@/pages/dashboard.vue'
import Produtos from '@/pages/produtos.vue'
import Entradas from '@/pages/entradas.vue'
import Vendas from '@/pages/vendas.vue'
import Movimentacoes from '@/pages/movimentacoes.vue'
import Relatorios from '@/pages/relatorios.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      component: Login,
    },
    {
      path: '/dashboard',
      component: Dashboard,
      meta: { requiresAuth: true },
    },
    {
      path: '/produtos',
      component: Produtos,
      meta: { requiresAuth: true },
    },
    {
      path: '/entradas',
      component: Entradas,
      meta: { requiresAuth: true },
    },
    {
      path: '/vendas',
      component: Vendas,
      meta: { requiresAuth: true },
    },
    {
      path: '/movimentacoes',
      component: Movimentacoes,
      meta: { requiresAuth: true },
    },
    {
      path: '/relatorios',
      component: Relatorios,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const requiresAuth = Boolean(to.meta?.requiresAuth)

  if (requiresAuth && !auth.isAuthenticated) {
    return { path: '/login' }
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
