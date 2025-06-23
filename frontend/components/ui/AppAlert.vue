<template>
  <div :class="alertClasses">
    <div class="flex">
      <div class="flex-shrink-0">
        <Icon v-if="icon" :name="icon" class="w-5 h-5" />
      </div>
      <div class="ml-3 flex-1">
        <h3 v-if="title" class="text-sm font-medium">
          {{ title }}
        </h3>
        <div v-if="description || $slots.description" class="mt-2 text-sm">
          <slot name="description">
            {{ description }}
          </slot>
        </div>
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, withDefaults, defineProps } from 'vue'

interface Props {
  color?: 'blue' | 'green' | 'red' | 'yellow'
  variant?: 'subtle' | 'solid'
  title?: string
  description?: string
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  color: 'blue',
  variant: 'subtle'
})

const alertClasses = computed(() => {
  const colors = {
    blue: 'alert-blue',
    green: 'alert-green',
    red: 'alert-red',
    yellow: 'bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4'
  }
  
  return colors[props.color]
})
</script>
