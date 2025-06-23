<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Left Panel: Settings -->
          <div class="lg:col-span-1">
            <GenerationSettings
              :current-time="currentTime"
            />
            
            <GenerationHistory
              class="mt-6"
            />
          </div>
          
          <!-- Right Panel: Results -->
          <div class="lg:col-span-2 space-y-6">
            <GenerationResults />
            
            <WeatherData
              :weather-data="selectedWeatherData"
              :is-batch-mode="isBatchMode"
              :batch-results="results"
              :selected-index="selectedWeatherIndex"
              @update:selectedIndex="selectedWeatherIndex = $event"
            />
          </div>
          
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// Import composables and utilities
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useLocationStore } from '~/stores/location'
import { useCommentStore } from '~/stores/comment'
import { useSettingsStore } from '~/stores/settings'

// Initialize stores
const locationStore = useLocationStore()
const commentStore = useCommentStore()
const settingsStore = useSettingsStore()

// State from stores
const { isBatchMode, selectedLocation, selectedLocations, locations } = storeToRefs(locationStore)
const { generating, result, results, history } = storeToRefs(commentStore)
const { selectedProvider, providers } = storeToRefs(settingsStore)

// Local state
const currentTime = ref('')
const selectedWeatherIndex = ref(0) // For selecting which weather data to show in batch mode

// Computed properties
const selectedWeatherData = computed(() => {
  if (!isBatchMode.value) {
    return result.value
  }
  
  if (results.value.length > 0 && selectedWeatherIndex.value < results.value.length) {
    return results.value[selectedWeatherIndex.value]
  }
  
  return null
})

// Methods - Keep only local methods that aren't handled by stores
const updateCurrentTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Time update interval reference
let timeUpdateInterval: NodeJS.Timeout | null = null

// Lifecycle
onMounted(() => {
  updateCurrentTime()
  timeUpdateInterval = setInterval(updateCurrentTime, 1000)
})

onUnmounted(() => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
    timeUpdateInterval = null
  }
})

// Watch for batch mode changes
watch(isBatchMode, (newValue) => {
  if (newValue) {
    commentStore.clearResults()
  } else {
    commentStore.clearResults()
    locationStore.deselectAllLocations()
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
