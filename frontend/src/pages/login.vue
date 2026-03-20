<template>
  <v-container fluid class="fill-height pa-6 bg-background">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6" xl="5">
        <v-card class="rounded-lg" elevation="1">
          <v-card-text class="pa-8">
            <div class="d-flex align-center mb-6">
              <v-avatar color="primary" variant="tonal" size="52">
                <v-icon icon="mdi-cube-outline" />
              </v-avatar>
              <div class="ml-4">
                <div class="text-h6 font-weight-bold">Batatã</div>
                <div class="text-body-2 text-medium-emphasis">Gestão de estoque e vendas</div>
              </div>
            </div>

            <v-form @submit.prevent="onSubmit">
              <v-text-field
                v-model="username"
                label="Usuário"
                autocomplete="username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                class="mb-2"
              />
              <v-text-field
                v-model="password"
                label="Senha"
                type="password"
                autocomplete="current-password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
              />

              <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
                {{ error }}
              </v-alert>

              <v-btn
                class="mt-6"
                block
                size="large"
                color="primary"
                type="submit"
                :loading="auth.loading"
              >
                Entrar
              </v-btn>
            </v-form>

            <div class="mt-6 text-caption text-medium-emphasis">
              Dica: se você acabou de iniciar, crie um usuário no admin do Django.
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
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
