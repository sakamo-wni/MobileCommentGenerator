<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Left Panel: Settings -->
          <div class="lg:col-span-1">
            <GenerationSettings
              :is-batch-mode="isBatchMode"
              :selected-location="selectedLocation"
              :selected-locations="selectedLocations"
              :selected-provider="selectedProvider"
              :locations="locations"
              :locations-loading="locationsLoading"
              :provider-options="providerOptions"
              :providers-loading="providersLoading"
              :generating="generating"
              :current-time="currentTime"
              @update:isBatchMode="isBatchMode = $event"
              @update:selectedLocation="selectedLocation = $event"
              @update:selectedLocations="selectedLocations = $event"
              @update:selectedProvider="selectedProvider = $event"
              @generate="generateComment"
              @select-all="selectAllLocations"
              @clear-all="clearAllLocations"
              @select-region="selectRegionLocations"
            />
            
            <GenerationHistory
              :history="history"
              class="mt-6"
            />
          </div>
          
          <!-- Right Panel: Results -->
          <div class="lg:col-span-2 space-y-6">
            <GenerationResults
              :generating="generating"
              :is-batch-mode="isBatchMode"
              :result="result"
              :results="results"
            />
            
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
import { getLocationsByRegion } from '~/constants/regions'

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// State management - 元の状態管理を完全復元
const isBatchMode = ref(false)
const selectedLocation = ref('東京')
const selectedLocations = ref<string[]>([])
const selectedProvider = ref({ label: 'Google Gemini', value: 'gemini' })
const generating = ref(false)
const result = ref(null)
const results = ref([])
const history = ref([])
const locations = ref([])
const locationsLoading = ref(false)
const providersLoading = ref(false)
const currentTime = ref('')
const selectedWeatherIndex = ref(0) // For selecting which weather data to show in batch mode

// Provider options
const providerOptions = ref([
  { label: 'OpenAI GPT', value: 'openai' },
  { label: 'Google Gemini', value: 'gemini' },
  { label: 'Anthropic Claude', value: 'anthropic' }
])

// Computed properties
const canGenerate = computed(() => {
  const hasLocation = isBatchMode.value 
    ? selectedLocations.value.length > 0
    : !!selectedLocation.value
  
  const hasProvider = !!selectedProvider.value
  const notGenerating = !generating.value
  
  return hasLocation && hasProvider && notGenerating
})

const selectedWeatherData = computed(() => {
  if (!isBatchMode.value) {
    return result.value
  }
  
  if (results.value.length > 0 && selectedWeatherIndex.value < results.value.length) {
    return results.value[selectedWeatherIndex.value]
  }
  
  return null
})

// Methods - 元のメソッドを完全復元
const generateComment = async () => {
  if (!canGenerate.value) return
  
  generating.value = true
  
  try {
    if (isBatchMode.value && selectedLocations.value.length > 0) {
      // Batch mode: Process multiple locations with parallel processing
      results.value = []
      selectedWeatherIndex.value = 0
      
      // Process in chunks for better performance
      const CONCURRENT_LIMIT = 3
      for (let i = 0; i < selectedLocations.value.length; i += CONCURRENT_LIMIT) {
        const chunk = selectedLocations.value.slice(i, i + CONCURRENT_LIMIT)
        
        const chunkPromises = chunk.map(async (location) => {
          try {
            const response = await $fetch(`${apiBaseUrl}/api/generate`, {
              method: 'POST',
              body: {
                location: location,
                llm_provider: selectedProvider.value.value,
                target_datetime: new Date().toISOString(),
                exclude_previous: false
              }
            })
            return response
          } catch (error) {
            console.error(`Failed to generate for ${location}:`, error)
            let errorMessage = 'Unknown error'
            if (error.name === 'AbortError') {
              errorMessage = 'タイムアウトしました（5秒以上）'
            } else if (error.message) {
              errorMessage = error.message
            }
            
            return {
              success: false,
              location: location,
              error: errorMessage
            }
          }
        })
        
        const chunkResults = await Promise.all(chunkPromises)
        results.value.push(...chunkResults)
      }

      // 履歴を更新
      for (const batchResult of results.value) {
        if (batchResult.success) {
          history.value.unshift({
            timestamp: new Date().toISOString(),
            location: batchResult.location,
            comment: batchResult.comment,
            provider: selectedProvider.value.label,
            success: true
          })
        }
      }
      
    } else {
      // Single mode
      const response = await $fetch(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        body: {
          location: selectedLocation.value,
          llm_provider: selectedProvider.value.value,
          target_datetime: new Date().toISOString(),
          exclude_previous: false
        }
      })
      
      result.value = response
      results.value = []
      
      // 履歴を更新
      if (response.success) {
        history.value.unshift({
          timestamp: new Date().toISOString(),
          location: selectedLocation.value,
          comment: response.comment,
          provider: selectedProvider.value.label,
          success: true
        })
      }
    }
  } catch (error) {
    console.error('Failed to generate comment:', error)
    
    if (isBatchMode.value) {
      results.value = [{
        success: false,
        location: '一括生成',
        error: 'コメント生成に失敗しました'
      }]
    } else {
      result.value = {
        success: false,
        location: selectedLocation.value,
        error: 'コメント生成に失敗しました'
      }
    }
  } finally {
    generating.value = false
  }
}

const selectAllLocations = () => {
  selectedLocations.value = [...locations.value]
}

const clearAllLocations = () => {
  selectedLocations.value = []
}

const selectRegionLocations = (region: string) => {
  const regionLocations = getLocationsByRegion(region)
  
  // Check if all locations from this region are already selected
  const allSelected = regionLocations.every(loc => selectedLocations.value.includes(loc))
  
  if (allSelected) {
    // Remove all locations from this region
    selectedLocations.value = selectedLocations.value.filter(loc => !regionLocations.includes(loc))
  } else {
    // Add missing locations from this region
    const newLocations = regionLocations.filter(loc => !selectedLocations.value.includes(loc))
    selectedLocations.value = [...selectedLocations.value, ...newLocations]
  }
}

const loadLocations = async () => {
  locationsLoading.value = true
  try {
    const response = await $fetch(`${apiBaseUrl}/api/locations`)
    locations.value = response.locations || []
  } catch (error) {
    console.error('Failed to load locations:', error)
    // Fallback to hardcoded locations
    locations.value = [
      '東京',
      '大阪',
      '名古屋',
      '札幌',
      '福岡',
      '仙台',
      '広島',
      '神戸',
      '京都',
      '横浜'
    ]
  } finally {
    locationsLoading.value = false
  }
}

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
onMounted(async () => {
  await loadLocations()
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
    result.value = null
  } else {
    results.value = []
    selectedLocations.value = []
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