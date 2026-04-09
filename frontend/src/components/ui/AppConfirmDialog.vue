<template>
  <AppModal :model-value="modelValue" :title="title" :description="description" :max-width="maxWidth" @update:modelValue="emit('update:modelValue', $event)">
    <div class="space-y-4">
      <div v-if="$slots.default" class="text-sm text-muted-foreground">
        <slot />
      </div>

      <div class="flex justify-end gap-3 border-t border-border pt-4">
        <AppButton variant="outline" @click="emit('update:modelValue', false)">{{ cancelText }}</AppButton>
        <AppButton :variant="confirmVariant" :loading="loading" @click="emit('confirm')">{{ confirmText }}</AppButton>
      </div>
    </div>
  </AppModal>
</template>

<script setup lang="ts">
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'

withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    description?: string
    confirmText?: string
    cancelText?: string
    confirmVariant?: 'primary' | 'outline' | 'ghost' | 'danger'
    loading?: boolean
    maxWidth?: 'md' | 'lg' | 'xl' | '2xl' | '4xl'
  }>(),
  {
    description: '',
    confirmText: 'Confirmar',
    cancelText: 'Cancelar',
    confirmVariant: 'danger',
    loading: false,
    maxWidth: 'md',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
}>()
</script>
