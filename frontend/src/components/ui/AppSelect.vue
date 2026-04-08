<template>
  <label class="block space-y-2">
    <span v-if="label" class="text-sm font-medium text-foreground">{{ label }}</span>
    <div class="relative">
      <span v-if="icon" class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-muted-foreground">
        <span :class="['mdi', icon, 'text-lg']" />
      </span>
      <select
        :value="normalizedValue"
        :disabled="disabled"
        class="h-11 w-full appearance-none rounded-[var(--radius)] border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-60"
        :class="[icon ? 'pl-10 pr-10' : 'pr-10', error ? 'border-error focus:border-error focus:ring-error/10' : 'border-border']"
        @change="onChange"
      >
        <option v-if="placeholder" value="">{{ placeholder }}</option>
        <option v-for="item in items" :key="String(item[itemValue])" :value="String(item[itemValue])">
          {{ item[itemTitle] }}
        </option>
      </select>
      <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground">
        <span class="mdi mdi-chevron-down text-lg" />
      </span>
    </div>
    <p v-if="error" class="text-xs text-error">{{ error }}</p>
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label?: string
    modelValue?: string | number | null
    items: Record<string, any>[]
    itemTitle?: string
    itemValue?: string
    placeholder?: string
    disabled?: boolean
    error?: string
    icon?: string
  }>(),
  {
    itemTitle: 'title',
    itemValue: 'value',
    placeholder: '',
    disabled: false,
    error: '',
    icon: '',
  },
)

const normalizedValue = computed(() => (props.modelValue == null ? '' : String(props.modelValue)))

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number | null): void
}>()

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement
  const value = target.value
  emit('update:modelValue', value === '' ? null : value)
}
</script>
