<template>
  <div class="mb-6">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      {{ isBatchMode ? '地点選択（複数選択可）' : '地点選択' }}
    </label>
    
    <!-- Single location mode -->
    <select 
      v-if="!isBatchMode"
      :value="selectedLocation"
      @change="$emit('update:selectedLocation', $event.target.value)"
      class="form-select"
      :disabled="locationsLoading"
    >
      <option value="">地点を選択...</option>
      <option v-for="location in locations" :key="location" :value="location">
        {{ location }}
      </option>
    </select>
    
    <!-- Batch mode -->
    <div v-else class="space-y-3">
      <!-- Quick select buttons -->
      <div class="space-y-2">
        <div class="flex flex-wrap gap-2">
          <AppButton 
            @click="$emit('selectAll')"
            size="xs" 
            variant="outline"
            icon="heroicons:check-circle"
            color="green"
          >
            🌍 全地点選択
          </AppButton>
          <AppButton 
            @click="$emit('clearAll')"
            size="xs" 
            variant="outline"
            icon="heroicons:x-circle"
            color="red"
          >
            クリア
          </AppButton>
        </div>
        
        <div class="text-xs font-medium text-gray-700 mb-1">地域選択:</div>
        <div class="flex flex-wrap gap-1">
          <AppButton 
            v-for="region in availableRegions"
            :key="region"
            @click="$emit('selectRegion', region)" 
            size="xs" 
            :variant="isRegionSelected(region) ? 'primary' : 'outline'"
          >
            {{ region }}
          </AppButton>
        </div>
      </div>
      
      <!-- Multiple select -->
      <select 
        multiple
        :value="selectedLocations"
        @change="updateSelectedLocations($event)"
        class="form-select h-32"
        :disabled="locationsLoading"
      >
        <option v-for="location in locations" :key="location" :value="location">
          {{ location }}
        </option>
      </select>
      
      <!-- Selected count -->
      <div class="text-sm text-gray-600">
        選択中: {{ selectedLocations.length }}地点
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, computed } from 'vue'
import { REGIONS, getLocationsByRegion, SIMPLIFIED_REGIONS } from '~/constants/regions'

interface Props {
  isBatchMode: boolean
  selectedLocation: string
  selectedLocations: string[]
  locations: string[]
  locationsLoading: boolean
}

interface Emits {
  'update:selectedLocation': [value: string]
  'update:selectedLocations': [value: string[]]
  'selectAll': []
  'clearAll': []
  'selectRegion': [region: string]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Get available regions from SIMPLIFIED_REGIONS for UI display
const availableRegions = computed(() => Object.keys(SIMPLIFIED_REGIONS))

const updateSelectedLocations = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selected = Array.from(target.selectedOptions).map(option => option.value)
  emit('update:selectedLocations', selected)
}

const isRegionSelected = (region: string) => {
  const regionLocations = getLocationsByRegion(region)
  return regionLocations.length > 0 && regionLocations.every(loc => props.selectedLocations.includes(loc))
}
</script>
