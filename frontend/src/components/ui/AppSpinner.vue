<template>
  <div class="flex items-center justify-center" :class="centered ? 'p-10' : ''">
    <div class="rounded-full border-4 border-primary/20 border-t-primary animate-spin" :class="sizeClass" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
    centered?: boolean
  }>(),
  {
    size: 'md',
    centered: true,
  },
)

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-5 w-5'
    case 'lg':
      return 'h-10 w-10'
    case 'md':
    default:
      return 'h-8 w-8'
  }
})
</script>
