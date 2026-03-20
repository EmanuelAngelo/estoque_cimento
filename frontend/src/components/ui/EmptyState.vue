<template>
  <div class="text-center py-12">
    <div class="w-16 h-16 rounded-[var(--radius)] bg-muted flex items-center justify-center mx-auto">
      <span :class="['mdi', icon, 'text-3xl', 'text-muted-foreground']" />
    </div>
    <h3 class="text-lg font-semibold text-foreground mt-4">{{ title }}</h3>
    <p v-if="description" class="text-muted-foreground mt-1 max-w-md mx-auto">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description?: string
}>()
</script>
