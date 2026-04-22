<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-[70] flex items-center justify-center p-3 sm:p-6">
      <div class="absolute inset-0 bg-black/45 backdrop-blur-[1px]" @click="emit('update:modelValue', false)" />
      <div
        class="relative z-10 flex w-full max-h-[calc(100vh-1.5rem)] flex-col overflow-hidden rounded-[calc(var(--radius)+0.25rem)] border border-border bg-card shadow-[0_24px_80px_-32px_rgba(15,23,42,0.5)] sm:max-h-[calc(100vh-3rem)]"
        :class="maxWidthClass"
      >
        <div class="flex items-start justify-between gap-4 border-b border-border px-6 py-5">
          <div>
            <h2 class="text-lg font-semibold text-foreground">{{ title }}</h2>
            <p v-if="description" class="mt-1 text-sm text-muted-foreground">{{ description }}</p>
          </div>
          <button
            type="button"
            class="inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius)] text-muted-foreground transition hover:bg-muted hover:text-foreground"
            @click="emit('update:modelValue', false)"
          >
            <span class="mdi mdi-close text-xl" />
          </button>
        </div>
        <div class="overflow-y-auto p-6">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    description?: string
    maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl'
  }>(),
  {
    description: '',
    maxWidth: '4xl',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const maxWidthClass = computed(() => {
  switch (props.maxWidth) {
    case 'sm':
      return 'max-w-sm'
    case 'md':
      return 'max-w-md'
    case 'lg':
      return 'max-w-2xl'
    case 'xl':
      return 'max-w-4xl'
    case '2xl':
      return 'max-w-5xl'
    case '4xl':
    default:
      return 'max-w-6xl'
  }
})
</script>
