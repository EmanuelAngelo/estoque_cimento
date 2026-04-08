<template>
  <div class="rounded-[var(--radius)] border px-4 py-3 text-sm leading-6" :class="variantClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'info' | 'success' | 'warning' | 'error'
  }>(),
  { variant: 'info' },
)

const variantClass = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'border-success/20 bg-success/10 text-success'
    case 'warning':
      return 'border-warning/20 bg-warning/10 text-warning'
    case 'error':
      return 'border-error/20 bg-error/10 text-error'
    case 'info':
    default:
      return 'border-info/20 bg-info/10 text-info'
  }
})
</script>
