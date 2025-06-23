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

// State management
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

// Methods
const generateComment = async () => {
  if (!canGenerate.value) return
  
  generating.value = true
  
  try {
    if (isBatchMode.value && selectedLocations.value.length > 0) {
      // Batch mode: Process multiple locations
      results.value = []
      selectedWeatherIndex.value = 0
      
      for (const location of selectedLocations.value) {
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
          
          results.value.push(response)
        } catch (error) {
          console.error(`Failed to generate for ${location}:`, error)
          let errorMessage = 'Unknown error'
          if (error.name === 'AbortError') {
            errorMessage = 'タイムアウトしました（5秒以上）'
          } else if (error.message) {
            errorMessage = error.message
          }
          
          results.value.push({
            success: false,
            location: location,
            error: `生成エラー: ${errorMessage}`,
            comment: null,
            advice_comment: null,
            metadata: null
          })
        }
      }
      
      // Add batch to history
      const successCount = results.value.filter(r => r.success).length
      history.value.unshift({
        timestamp: new Date().toISOString(),
        location: `${selectedLocations.value.length}地点 (成功: ${successCount})`,
        provider: selectedProvider.value?.label || 'Unknown',
        success: successCount > 0
      })
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
      
      // Add to history
      history.value.unshift({
        timestamp: new Date().toISOString(),
        location: selectedLocation.value,
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
        results.value = [{
          success: false,
          error: 'バッチ処理の開始に失敗しました',
          location: '不明'
        }]
      }
    } else {
      result.value = {
        success: false,
        error: 'Generation failed',
        location: selectedLocation.value
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
  const newSelections = regionLocations.filter(loc => locations.value.includes(loc))
  
  // Toggle region selection
  const allSelected = newSelections.every(loc => selectedLocations.value.includes(loc))
  if (allSelected) {
    selectedLocations.value = selectedLocations.value.filter(loc => !newSelections.includes(loc))
  } else {
    selectedLocations.value = [...new Set([...selectedLocations.value, ...newSelections])]
  }
}

const loadLocations = async () => {
  console.log('Starting loadLocations...')
  locationsLoading.value = true
  
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
    locations.value = response.locations || []
  } catch (error) {
    let errorMessage = '地点データの取得に失敗しました'
    if (error.name === 'AbortError') {
      errorMessage = 'API接続がタイムアウトしました（5秒以上）'
      console.error('API request timeout')
    } else {
      console.error('Failed to load locations:', error)
    }
    
    console.log('Using fallback location list...')
    locations.value = [
      '札幌', '函館', '旭川', '青森', '秋田', '盛岡', '山形', '仙台', '福島',
      '新潟', '富山', '金沢', '福井', '水戸', '宇都宮', '前橋', 'さいたま',
      '千葉', '東京', '横浜', '甲府', '長野', '岐阜', '静岡', '名古屋', '津',
      '大津', '京都', '大阪', '神戸', '奈良', '和歌山', '鳥取', '松江',
      '岡山', '広島', '山口', '徳島', '高松', '松山', '高知', '福岡',
      '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '那覇'
    ]
    
    // TODO: ユーザーに通知を表示する仕組みを追加
  } finally {
    console.log('Setting locationsLoading to false, locations count:', locations.value.length)
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
  updateCurrentTime()
  timeUpdateInterval = setInterval(updateCurrentTime, 1000)
  
  await loadLocations()
  
  // Set default selections
  if (locations.value.length > 0) {
    selectedLocation.value = locations.value[0]
  }
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
