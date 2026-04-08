<template>
  <label class="block space-y-2">
    <span v-if="label" class="text-sm font-medium text-foreground">{{ label }}</span>
    <div class="relative">
      <span v-if="icon" class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
        <span :class="['mdi', icon, 'text-lg']" />
      </span>
      <input
        :value="modelValue"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :min="min"
        :step="step"
        :autocomplete="autocomplete"
        class="h-11 w-full rounded-[var(--radius)] border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
        :class="[icon ? 'pl-10' : '', error ? 'border-error focus:border-error focus:ring-error/10' : 'border-border']"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <p v-if="error" class="text-xs text-error">{{ error }}</p>
  </label>
</template>

<script setup lang="ts">
defineProps<{
  label?: string
  modelValue?: string | number | null
  type?: string
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  error?: string
  icon?: string
  min?: string | number
  step?: string | number
  autocomplete?: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>
