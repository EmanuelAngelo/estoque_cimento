import { defineStore } from 'pinia'
import api from '@/api/client'

export type AuthUser = {
  id: number
  username: string
  first_name: string
  last_name: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: (localStorage.getItem('auth_token') ?? '') as string,
    user: (localStorage.getItem('auth_user')
      ? (JSON.parse(localStorage.getItem('auth_user') as string) as AuthUser)
      : null) as AuthUser | null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    async login(username: string, password: string) {
      this.loading = true
      try {
        const { data } = await api.post('/auth/login/', { username, password })
        this.token = data.token
        this.user = data.user
        localStorage.setItem('auth_token', this.token)
        localStorage.setItem('auth_user', JSON.stringify(this.user))
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.loading = true
      try {
        await api.post('/auth/logout/')
      } catch {
        // ignore
      } finally {
        this.token = ''
        this.user = null
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        this.loading = false
      }
    },

    async fetchMe() {
      if (!this.token) return
      const { data } = await api.get('/auth/me/')
      this.user = data
      localStorage.setItem('auth_user', JSON.stringify(this.user))
    },
  },
})
