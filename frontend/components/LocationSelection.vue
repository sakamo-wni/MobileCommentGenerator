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
        <!-- Region Selection -->
        <div class="region-selection">
          <label for="region-select">地方選択:</label>
          <div class="custom-dropdown">
            <select 
              id="region-select"
              v-model="selectedRegion"
              @change="handleRegionChange"
              class="region-select"
            >
              <option value="">すべての地方</option>
              <option v-for="region in regions" :key="region" :value="region">
                {{ region }}
              </option>
            </select>
            <div class="dropdown-arrow">▼</div>
          </div>
        </div>

        <!-- Select All Controls -->
        <div class="select-all-section">
          <div class="select-all-controls">
            <button 
              @click="selectAllLocations" 
              class="control-btn select-all-btn"
              :disabled="filteredLocations.length === 0"
            >
              すべて選択
            </button>
            <button 
              @click="clearAllSelections" 
              class="control-btn clear-all-btn"
              :disabled="selectedLocations.length === 0"
            >
              すべてクリア
            </button>
            <button 
              @click="selectRegionLocations" 
              class="control-btn region-btn"
              :disabled="!selectedRegion || getRegionLocations().length === 0"
            >
              {{ selectedRegion || '地方' }}を選択
            </button>
          </div>
          <div class="selection-info">
            <span class="selection-count">{{ selectedLocations.length }}地点選択中</span>
            <span class="total-count">/ {{ filteredLocations.length }}地点</span>
          </div>
        </div>

        <!-- Location Grid -->
        <div class="location-grid">
          <div 
            v-for="location in filteredLocations" 
            :key="location.name"
            class="location-item"
            :class="{ selected: selectedLocations.includes(location.name) }"
            @click="toggleLocation(location.name)"
          >
            <div class="location-checkbox">
              <input 
                type="checkbox" 
                :checked="selectedLocations.includes(location.name)"
                @click.stop
                readonly
              />
            </div>
            <div class="location-details">
              <span class="location-name">{{ location.name }}</span>
              <span class="location-region">{{ location.region || getAreaName(location.name) }}</span>
            </div>
          </div>
        </div>

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
import { ref, computed, onMounted, onUnmounted, reactive, toRefs, watch } from 'vue'
import { useApi } from '~/composables/useApi'
import type { Location } from '~/types'
import { 
  createLocationSelectionLogic, 
  REGIONS,
  getAreaName 
} from '@mobile-comment-generator/shared/composables'

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

// Local state
const regions = ref(REGIONS)

// Computed
const locations = computed(() => {
  return allLocations.value.map(loc => loc.name)
})

const filteredLocations = computed(() => {
  const result = locationLogic.getFilteredLocations()
  if (result.length === 0 && allLocations.value.length > 0) {
    console.warn('filteredLocations is empty but allLocations has data:', {
      allLocationsLength: allLocations.value.length,
      selectedRegion: locationLogic.selectedRegion,
      locationsInLogic: locationLogic.locations.length
    })
  }
  return result
})

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