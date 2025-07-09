<template>
  <div class="location-selection">
    <div class="component-header">
      <h3>地点選択</h3>
    </div>
    
    <div class="selection-content">
      <!-- Loading state -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>地点データを読み込み中...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="loadLocations" class="retry-btn">再読み込み</button>
      </div>

      <!-- Main content -->
      <template v-else>
        <LocationSelectionControls
          :regions="regions"
          :selected-region="selectedRegion"
          :selected-count="selectedLocations.length"
          :filtered-count="locationLogic.getFilteredLocations().length"
          :region-location-count="getRegionLocations().length"
          @region-change="selectedRegion = $event; handleRegionChange()"
          @select-all="selectAllLocations"
          @clear-all="clearAllSelections"
          @select-region="selectRegionLocations"
        />

        <!-- Location Grid -->
        <LocationSelectionGrid
          :locations="locationLogic.getFilteredLocations()"
          :selected-locations="selectedLocations"
          @toggle="toggleLocation"
        />

        <!-- Selected Locations Summary -->
        <div class="selected-summary" v-if="selectedLocations.length > 0">
          <h4>選択済み地点 ({{ selectedLocations.length }})</h4>
          <div class="selected-tags">
            <span 
              v-for="location in selectedLocations.slice(0, 10)" 
              :key="location"
              class="location-tag"
              @click="toggleLocation(location)"
            >
              {{ location }}
              <span class="remove-tag">×</span>
            </span>
            <span v-if="selectedLocations.length > 10" class="more-locations">
              他{{ selectedLocations.length - 10 }}地点...
            </span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, toRefs, watch, onMounted, onUnmounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { 
  createLocationSelectionLogic, 
  REGIONS,
  getAreaName 
} from '@mobile-comment-generator/shared/composables'
import LocationSelectionControls from './LocationSelectionControls.vue'
import LocationSelectionGrid from './LocationSelectionGrid.vue'

// Props
interface Props {
  selectedLocation?: string
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'location-changed', location: string): void
  (e: 'locations-changed', locations: string[]): void
}

const emit = defineEmits<Emits>()

// API composable
const api = useApi()

// 共通ロジックを使用
const locationLogic = reactive(createLocationSelectionLogic())

// 共通ロジックのAPIクライアントを設定
locationLogic.setApiClient({
  fetchLocations: async () => {
    const response = await api.fetchLocations()
    return {
      success: response.success,
      data: response.data?.map(loc => ({
        ...loc,
        id: loc.name,
        prefecture: '',
        region: loc.area || getAreaName(loc.name),
      }))
    }
  }
})

// Reactive references
const { 
  locations: allLocations,
  selectedLocations,
  isLoading,
  error,
  selectedRegion
} = toRefs(locationLogic)

// Computed
const regions = REGIONS

// Methods wrapper
const loadLocations = async () => {
  await locationLogic.loadLocations()
  emitLocationChanges()
}

const toggleLocation = (location: string) => {
  locationLogic.toggleLocation(location)
  emitLocationChanges()
}

const selectAllLocations = () => {
  locationLogic.selectAllLocations()
  emitLocationChanges()
}

const clearAllSelections = () => {
  locationLogic.clearAllSelections()
  emitLocationChanges()
}

const selectRegionLocations = () => {
  if (selectedRegion.value) {
    locationLogic.selectRegionLocations(selectedRegion.value)
    emitLocationChanges()
  }
}

const handleRegionChange = () => {
  locationLogic.setSelectedRegion(selectedRegion.value)
}

const getRegionLocations = () => {
  return selectedRegion.value 
    ? locationLogic.getRegionLocations(selectedRegion.value)
    : []
}

const emitLocationChanges = () => {
  emit('locations-changed', selectedLocations.value)
  
  if (selectedLocations.value.length > 0) {
    emit('location-changed', selectedLocations.value[0])
  }
}

// Watch for selectedRegion changes
const stopRegionWatcher = watch(selectedRegion, () => {
  handleRegionChange()
})

// Lifecycle
onMounted(() => {
  loadLocations()
})

// Cleanup
onUnmounted(() => {
  stopRegionWatcher()
})
</script>

<style scoped>
.location-selection {
  background: linear-gradient(135deg, #E8F0FE 0%, #F3F8FF 100%);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 12px rgba(12, 65, 154, 0.1);
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Loading and Error states */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  min-height: 400px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E8F0FE;
  border-top-color: #0C419A;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #0C419A;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.retry-btn:hover {
  background: #1a52b3;
}

/* Component styles continue... */
</style>