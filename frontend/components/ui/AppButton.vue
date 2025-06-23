<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <Icon v-if="loading" name="heroicons:arrow-path" class="w-4 h-4 animate-spin mr-2" />
    <Icon v-else-if="icon" :name="icon" class="w-4 h-4 mr-2" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed, withDefaults, defineProps, defineEmits } from 'vue'

interface Props {
  variant?: 'primary' | 'outline' | 'ghost' | 'green' | 'red' | 'gray'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  icon?: string
  block?: boolean
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md'
})

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 rounded-lg'
  
  const variants = {
    primary: 'btn-primary',
    outline: 'btn-outline',
    ghost: 'hover:bg-gray-100',
    green: 'btn-green',
    red: 'btn-red',
    gray: 'btn-gray'
  }
  
  const sizes = {
    xs: 'btn-xs',
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg'
  }
  
  return [
    base,
    variants[props.variant],
    sizes[props.size],
    props.block ? 'w-full' : '',
  ].filter(Boolean).join(' ')
})

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>
