<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center gap-2 rounded-[var(--radius)] font-medium transition focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-60"
    :class="[sizeClass, variantClass]"
  >
    <span v-if="loading" class="h-4 w-4 animate-spin rounded-full border-2 border-current/25 border-t-current" />
    <span v-else-if="icon" :class="['mdi', icon, iconSizeClass]" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'button' | 'submit' | 'reset'
    variant?: 'primary' | 'outline' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    icon?: string
    loading?: boolean
    disabled?: boolean
  }>(),
  {
    type: 'button',
    variant: 'primary',
    size: 'md',
    icon: '',
    loading: false,
    disabled: false,
  },
)

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-9 px-3 text-sm'
    case 'lg':
      return 'h-12 px-5 text-sm'
    case 'md':
    default:
      return 'h-10 px-4 text-sm'
  }
})

const iconSizeClass = computed(() => (props.size === 'lg' ? 'text-lg' : 'text-base'))

const variantClass = computed(() => {
  switch (props.variant) {
    case 'outline':
      return 'border border-border bg-card text-foreground hover:bg-muted focus:ring-primary/10'
    case 'ghost':
      return 'text-foreground hover:bg-muted focus:ring-primary/10'
    case 'danger':
      return 'bg-error text-white hover:brightness-110 focus:ring-error/20 shadow-sm'
    case 'primary':
    default:
      return 'bg-primary text-primary-foreground hover:brightness-110 focus:ring-primary/20 shadow-sm'
  }
})
</script>
