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
              @update:isBatchMode="locationStore.setBatchMode($event)"
              @update:selectedLocation="locationStore.setSelectedLocation($event)"
              @update:selectedLocations="locationStore.setSelectedLocations($event)"
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
import { storeToRefs } from 'pinia'
import { getLocationsByRegion } from '~/constants/regions'
import { useCommentStore } from '~/stores/comment'
import { useLocationStore } from '~/stores/location'

// Runtime config
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl || 'http://localhost:8000'

// Pinia store initialization
const commentStore = useCommentStore()
const locationStore = useLocationStore()
const { generating, result, results } = storeToRefs(commentStore)
const { 
  selectedLocation, 
  selectedLocations, 
  isBatchMode,
  locations,
  locationsLoading,
  canGenerate 
} = storeToRefs(locationStore)

// State management (non-location related)
const selectedProvider = ref({ label: 'Google Gemini', value: 'gemini' })
// generating, result, results are now managed by commentStore
// selectedLocation, selectedLocations, isBatchMode, locations, locationsLoading are now managed by locationStore
const history = ref([])
const providersLoading = ref(false)
const currentTime = ref('')
const selectedWeatherIndex = ref(0) // For selecting which weather data to show in batch mode

// Provider options
const providerOptions = ref([
  { label: 'OpenAI GPT', value: 'openai' },
  { label: 'Google Gemini', value: 'gemini' },
  { label: 'Anthropic Claude', value: 'anthropic' }
])

// Computed properties (updated to use locationStore canGenerate + provider check)
const canGenerateWithProvider = computed(() => {
  const hasProvider = !!selectedProvider.value
  const notGenerating = !generating.value
  
  return locationStore.canGenerate && hasProvider && notGenerating
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

// Methods
const generateComment = async () => {
  if (!canGenerateWithProvider.value) return
  
  commentStore.setGenerating(true)
  commentStore.clearResults()
  
  try {
    if (locationStore.isBatchMode && locationStore.selectedLocations.length > 0) {
      // Batch mode: Use new bulk generation endpoint
      selectedWeatherIndex.value = 0
      
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 120000) // 2分のタイムアウト
        
        const response = await $fetch(`${apiBaseUrl}/api/generate/bulk`, {
          method: 'POST',
          body: {
            locations: locationStore.selectedLocations,
            llm_provider: selectedProvider.value.value
          },
          signal: controller.signal,
          timeout: 120000 // 2分のタイムアウトを明示的に設定
        })
        
        clearTimeout(timeoutId)
        
        // Add all results to store
        if (response.results) {
          response.results.forEach(result => commentStore.addResult(result))
        }
      } catch (error) {
        console.error('Bulk generation failed:', error)
        let errorMessage = 'Unknown error'
        if (error.name === 'AbortError') {
          errorMessage = 'タイムアウトしました（2分以上）'
        } else if (error.message) {
          errorMessage = error.message
        }
        
        // Add error result for all locations
        locationStore.selectedLocations.forEach(location => {
          commentStore.addResult({
            success: false,
            location: location,
            error: `一括生成エラー: ${errorMessage}`,
            comment: null,
            advice_comment: null,
            metadata: null
          })
        })
      }
      
      // Add batch to history
      const successCount = results.value.filter(r => r.success).length
      history.value.unshift({
        timestamp: new Date().toISOString(),
        location: `${locationStore.selectedLocations.length}地点 (成功: ${successCount})`,
        provider: selectedProvider.value?.label || 'Unknown',
        success: successCount > 0
      })
    } else {
      // Single mode
      const response = await $fetch(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        body: {
          location: locationStore.selectedLocation,
          llm_provider: selectedProvider.value.value,
          target_datetime: new Date().toISOString(),
          exclude_previous: false
        }
      })
      
      commentStore.setResult(response)
      
      // Add to history
      history.value.unshift({
        timestamp: new Date().toISOString(),
        location: locationStore.selectedLocation,
        provider: selectedProvider.value?.label || 'Unknown',
        success: response.success
      })
    }
    
  } catch (error) {
    console.error('Generation failed:', error)
    if (isBatchMode.value) {
      // In batch mode, errors should have been handled per location
      // This catch is for unexpected errors
      if (results.value.length === 0) {
        commentStore.addResult({
          success: false,
          error: 'バッチ処理の開始に失敗しました',
          location: '不明'
        })
      }
    } else {
      commentStore.setResult({
        success: false,
        error: 'Generation failed',
        location: selectedLocation.value
      })
    }
  } finally {
    commentStore.setGenerating(false)
  }
}

const selectAllLocations = () => {
  locationStore.selectAllLocations()
}

const clearAllLocations = () => {
  locationStore.clearAllLocations()
}

const selectRegionLocations = (region: string) => {
  locationStore.selectRegionLocations(region)
}

const loadLocations = async () => {
  console.log('Starting loadLocations...')
  locationStore.setLocationsLoading(true)
  
  try {
    console.log('Attempting to fetch from /api/locations...')
    // Add timeout to prevent hanging indefinitely
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
    
    const response = await $fetch(`${apiBaseUrl}/api/locations`, {
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    
    console.log('API response received:', response)
    locationStore.setLocations(response.locations || [])
  } catch (error) {
    let errorMessage = '地点データの取得に失敗しました'
    if (error.name === 'AbortError') {
      errorMessage = 'API接続がタイムアウトしました（5秒以上）'
      console.error('API request timeout')
    } else {
      console.error('Failed to load locations:', error)
    }
    
    console.log('Using fallback location list...')
    locationStore.setLocations([
      '札幌', '函館', '旭川', '青森', '秋田', '盛岡', '山形', '仙台', '福島',
      '新潟', '富山', '金沢', '福井', '水戸', '宇都宮', '前橋', 'さいたま',
      '千葉', '東京', '横浜', '甲府', '長野', '岐阜', '静岡', '名古屋', '津',
      '大津', '京都', '大阪', '神戸', '奈良', '和歌山', '鳥取', '松江',
      '岡山', '広島', '山口', '徳島', '高松', '松山', '高知', '福岡',
      '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '那覇'
    ])
    
    // TODO: ユーザーに通知を表示する仕組みを追加
  } finally {
    console.log('Setting locationsLoading to false, locations count:', locationStore.locations.length)
    locationStore.setLocationsLoading(false)
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
  updateCurrentTime()
  timeUpdateInterval = setInterval(updateCurrentTime, 1000)
  
  await loadLocations()
  
  // Set default selections
  if (locationStore.locations.length > 0) {
    locationStore.setSelectedLocation(locationStore.locations[0])
  }
})

onUnmounted(() => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
    timeUpdateInterval = null
  }
})

// Watch for batch mode changes (comment/result clearing only - location clearing handled by store)
watch(isBatchMode, (newValue) => {
  if (newValue) {
    commentStore.setResult(null)
  } else {
    commentStore.setResults([])
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
