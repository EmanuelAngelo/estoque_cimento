<template>
  <div class="app-card p-6">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm text-muted-foreground">{{ label }}</p>
        <p class="text-2xl font-bold text-foreground mt-1">{{ value }}</p>
        <p v-if="subtitle" class="text-xs text-muted-foreground mt-1">{{ subtitle }}</p>
      </div>
      <div class="w-12 h-12 rounded-[var(--radius)] flex items-center justify-center" :class="iconClass">
        <span :class="['mdi', icon, 'text-2xl']" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: string
  subtitle?: string
  icon: string
  variant?: 'primary' | 'accent' | 'success' | 'info'
}>()

const iconClass = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-success/10 text-success'
    case 'accent':
      return 'bg-accent/10 text-accent'
    case 'info':
      return 'bg-info/10 text-info'
    case 'primary':
    default:
      return 'bg-primary/10 text-primary'
  }
})
</script>
