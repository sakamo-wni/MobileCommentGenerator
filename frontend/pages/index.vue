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
          <div class="lg:col-span-2">
            <GenerationResults
              :generating="generating"
              :is-batch-mode="isBatchMode"
              :result="result"
              :results="results"
            />
          </div>
          
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
// Import composables and utilities
import { ref, computed, onMounted, watch } from 'vue'

// State management
const isBatchMode = ref(false)
const selectedLocation = ref('')
const selectedLocations = ref<string[]>([])
const selectedProvider = ref(null)
const generating = ref(false)
const result = ref(null)
const results = ref([])
const history = ref([])
const locations = ref([])
const locationsLoading = ref(false)
const providersLoading = ref(false)
const currentTime = ref('')

// Provider options
const providerOptions = ref([
  { label: 'OpenAI GPT-4', value: 'openai-gpt4' },
  { label: 'OpenAI GPT-3.5', value: 'openai-gpt35' },
  { label: 'Anthropic Claude', value: 'anthropic-claude' },
  { label: 'Google Gemini', value: 'google-gemini' }
])

// Computed properties
const canGenerate = computed(() => {
  return (isBatchMode.value && selectedLocations.value.length > 0) || 
         (!isBatchMode.value && selectedLocation.value) && 
         selectedProvider.value && 
         !generating.value
})

// Methods
const generateComment = async () => {
  if (!canGenerate.value) return
  
  generating.value = true
  
  try {
    const response = await $fetch('/api/generate', {
      method: 'POST',
      body: {
        isBatchMode: isBatchMode.value,
        location: selectedLocation.value,
        locations: selectedLocations.value,
        provider: selectedProvider.value
      }
    })
    
    if (isBatchMode.value) {
      results.value = response.results
    } else {
      result.value = response
    }
    
    // Add to history
    history.value.unshift({
      timestamp: new Date().toISOString(),
      location: isBatchMode.value ? 'Multiple' : selectedLocation.value,
      provider: selectedProvider.value.label,
      success: isBatchMode.value ? response.results.some(r => r.success) : response.success
    })
    
  } catch (error) {
    console.error('Generation failed:', error)
    if (isBatchMode.value) {
      results.value = []
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
  const regionMap: Record<string, string[]> = {
    '北海道': ['札幌', '函館', '旭川'],
    '東北': ['青森', '秋田', '盛岡', '山形', '仙台', '福島'],
    '北陸': ['新潟', '富山', '金沢', '福井'],
    '関東': ['水戸', '宇都宮', '前橋', 'さいたま', '千葉', '東京', '横浜'],
    '甲信': ['甲府', '長野'],
    '東海': ['岐阜', '静岡', '名古屋', '津'],
    '近畿': ['大津', '京都', '大阪', '神戸', '奈良', '和歌山'],
    '中国': ['鳥取', '松江', '岡山', '広島', '山口'],
    '四国': ['徳島', '高松', '松山', '高知'],
    '九州': ['福岡', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島'],
    '沖縄': ['那覇']
  }
  
  const regionLocations = regionMap[region] || []
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
    
    const response = await $fetch('/api/locations', {
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    
    console.log('API response received:', response)
    locations.value = response.locations || []
  } catch (error) {
    console.error('Failed to load locations:', error)
    console.log('Using fallback location list...')
    locations.value = [
      '札幌', '函館', '旭川', '青森', '秋田', '盛岡', '山形', '仙台', '福島',
      '新潟', '富山', '金沢', '福井', '水戸', '宇都宮', '前橋', 'さいたま',
      '千葉', '東京', '横浜', '甲府', '長野', '岐阜', '静岡', '名古屋', '津',
      '大津', '京都', '大阪', '神戸', '奈良', '和歌山', '鳥取', '松江',
      '岡山', '広島', '山口', '徳島', '高松', '松山', '高知', '福岡',
      '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '那覇'
    ]
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

// Lifecycle
onMounted(async () => {
  updateCurrentTime()
  setInterval(updateCurrentTime, 1000)
  
  await loadLocations()
  
  // Set default selections
  if (locations.value.length > 0) {
    selectedLocation.value = locations.value[0]
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
