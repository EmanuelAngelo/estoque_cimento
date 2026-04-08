<template>
  <label class="block space-y-2">
    <span v-if="label" class="text-sm font-medium text-foreground">{{ label }}</span>
    <textarea
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      class="w-full rounded-[var(--radius)] border bg-background px-3 py-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
      :class="error ? 'border-error focus:border-error focus:ring-error/10' : 'border-border'"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <p v-if="error" class="text-xs text-error">{{ error }}</p>
  </label>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string
    modelValue?: string | null
    placeholder?: string
    disabled?: boolean
    error?: string
    rows?: number
  }>(),
  {
    placeholder: '',
    disabled: false,
    error: '',
    rows: 3,
  },
)

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>
