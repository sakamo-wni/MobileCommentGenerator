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
              @retry="retryFailedLocation"
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
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { getLocationsByRegion } from '~/constants/regions'
import { useCommentStore } from '~/stores/comment'
import { useLocationStore } from '~/stores/location'
import { BATCH_CONFIG } from '../../src/config/constants'
import { getErrorMessage, logError } from '~/utils/error'

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
      // Batch mode: Process locations in chunks for progressive display
      selectedWeatherIndex.value = 0
      
      // Initialize results with placeholders to maintain order
      const placeholderResults = locationStore.selectedLocations.map(location => ({
        success: false,
        location: location,
        comment: null,
        advice_comment: null,
        metadata: null,
        loading: true
      }))
      commentStore.setResults(placeholderResults)
      
      // Process in chunks for better performance and progressive display
      // This limits the number of simultaneous requests to prevent overwhelming the server
      // and provides incremental updates to the UI every CONCURRENT_LIMIT locations
      for (let i = 0; i < locationStore.selectedLocations.length; i += BATCH_CONFIG.CONCURRENT_LIMIT) {
        const chunk = locationStore.selectedLocations.slice(i, i + BATCH_CONFIG.CONCURRENT_LIMIT)
        
        const chunkPromises = chunk.map(async (location, chunkIdx) => {
          const globalIdx = i + chunkIdx
          try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), BATCH_CONFIG.REQUEST_TIMEOUT)
            
            const response = await $fetch(`${apiBaseUrl}/api/generate`, {
              method: 'POST',
              body: {
                location: location,
                llm_provider: selectedProvider.value.value,
                target_datetime: new Date().toISOString(),
                exclude_previous: false
              },
              signal: controller.signal,
              timeout: BATCH_CONFIG.REQUEST_TIMEOUT
            })
            
            clearTimeout(timeoutId)
            
            // Update result at specific index for progressive display
            const successResult = {
              ...response,
              loading: false
            }
            commentStore.updateResultAtIndex(globalIdx, successResult)
            return successResult
          } catch (error) {
            logError(error, `${location}のコメント生成`)
            const errorMessage = getErrorMessage({ 
              error, 
              context: `${location}のコメント生成`
            })
            
            const errorResult = {
              success: false,
              location: location,
              error: `生成エラー: ${errorMessage}`,
              comment: null,
              advice_comment: null,
              metadata: null,
              loading: false
            }
            
            // Update error result at specific index
            commentStore.updateResultAtIndex(globalIdx, errorResult)
            return errorResult
          }
        })
        
        // Wait for all requests in the chunk to complete before processing next chunk
        // We use individual addResult calls instead of batch addResults to ensure
        // immediate progressive display as each location completes
        await Promise.allSettled(chunkPromises)
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
    logError(error, 'コメント生成')
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

const retryFailedLocation = async (location: string, index: number) => {
  console.log(`Retrying generation for ${location} at index ${index}`)
  
  // Mark as loading
  commentStore.updateResultAtIndex(index, {
    success: false,
    location: location,
    comment: null,
    advice_comment: null,
    metadata: null,
    loading: true,
    error: null
  })
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120000) // 2分のタイムアウト
    
    const response = await $fetch(`${apiBaseUrl}/api/generate`, {
      method: 'POST',
      body: {
        location: location,
        llm_provider: selectedProvider.value.value,
        target_datetime: new Date().toISOString(),
        exclude_previous: false
      },
      signal: controller.signal,
      timeout: BATCH_CONFIG.REQUEST_TIMEOUT
    })
    
    clearTimeout(timeoutId)
    
    // Update with success result
    const successResult = {
      ...response,
      loading: false
    }
    commentStore.updateResultAtIndex(index, successResult)
  } catch (error) {
    logError(error, `${location}の再試行`)
    const errorMessage = getErrorMessage({ 
      error, 
      context: `${location}の再試行`
    })
    
    // Update with error result
    const errorResult = {
      success: false,
      location: location,
      error: `生成エラー: ${errorMessage}`,
      comment: null,
      advice_comment: null,
      metadata: null,
      loading: false
    }
    commentStore.updateResultAtIndex(index, errorResult)
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
    logError(error, '地点データの取得')
    const errorMessage = getErrorMessage({ 
      error, 
      context: '地点データの取得'
    })
    
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

// Ensure interval is cleared before component unmount
onBeforeUnmount(() => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
    timeUpdateInterval = null
  }
})

onUnmounted(() => {
  // Double-check cleanup
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
