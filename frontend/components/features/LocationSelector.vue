<template>
  <div class="mb-6">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      {{ isBatchMode ? '地点選択（複数選択可）' : '地点選択' }}
    </label>
    
    <!-- Single location mode -->
    <select 
      v-if="!isBatchMode"
      :value="selectedLocation"
      @change="locationStore.selectedLocation = ($event.target as HTMLSelectElement).value"
      class="form-select"
      :disabled="false"
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
            @click="locationStore.selectAllLocations()"
            size="xs" 
            variant="outline"
            icon="heroicons:check-circle"
            color="green"
          >
            🌍 全地点選択
          </AppButton>
          <AppButton 
            @click="locationStore.deselectAllLocations()"
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
            @click="selectRegion(region)" 
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
        :disabled="false"
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
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { REGIONS, getLocationsByRegion, SIMPLIFIED_REGIONS } from '~/constants/regions'
import { useLocationStore } from '~/stores/location'

const locationStore = useLocationStore()
const { 
  isBatchMode, 
  selectedLocation, 
  selectedLocations, 
  locations 
} = storeToRefs(locationStore)

// Get available regions from SIMPLIFIED_REGIONS for UI display
const availableRegions = computed(() => Object.keys(SIMPLIFIED_REGIONS))

const updateSelectedLocations = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selected = Array.from(target.selectedOptions).map(option => option.value)
  // Clear current selections and set new ones
  locationStore.clearSelection()
  for (const location of selected) {
    locationStore.selectLocation(location)
  }
}

const isRegionSelected = (region: string) => {
  const regionLocations = getLocationsByRegion(region)
  return regionLocations.length > 0 && regionLocations.every(loc => selectedLocations.value.includes(loc))
}

// 地域選択機能
const selectRegion = (region: string) => {
  const regionLocations = getLocationsByRegion(region)
  for (const location of regionLocations) {
    if (locations.value.includes(location) && !selectedLocations.value.includes(location)) {
      locationStore.selectLocation(location)
    }
  }
}
</script>
