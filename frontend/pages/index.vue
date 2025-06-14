<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <UIcon name="i-heroicons-sun" class="w-8 h-8 text-yellow-500 mr-3" />
            <h1 class="text-xl font-bold text-gray-900">天気コメント生成システム</h1>
          </div>
          <UBadge color="blue" variant="subtle">
            Version 1.0.0
          </UBadge>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div class="px-4 py-6 sm:px-0">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Left Panel: Settings -->
          <div class="lg:col-span-1">
            <UCard>
              <template #header>
                <div class="flex items-center">
                  <UIcon name="i-heroicons-cog-6-tooth" class="w-5 h-5 mr-2" />
                  <h2 class="text-lg font-semibold">設定</h2>
                </div>
              </template>

              <!-- Batch Mode Toggle -->
              <div class="mb-6">
                <UFormGroup label="生成モード" class="mb-4">
                  <div class="p-4 border-2 border-gray-200 rounded-lg bg-white hover:border-blue-300 transition-colors">
                    <div class="flex items-center justify-between">
                      <div class="flex-1">
                        <div class="text-lg font-semibold text-gray-900 mb-1">
                          {{ isBatchMode ? '🌏 一括生成モード' : '📍 単一地点モード' }}
                        </div>
                        <div class="text-sm text-gray-600">
                          {{ isBatchMode ? '複数地点を同時に生成します' : '1つの地点のみ生成します' }}
                        </div>
                      </div>
                      <div class="relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out"
                           :class="isBatchMode ? 'bg-blue-500' : 'bg-gray-300'"
                           @click="isBatchMode = !isBatchMode">
                        <span class="pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                              :class="isBatchMode ? 'translate-x-6' : 'translate-x-0'">
                        </span>
                      </div>
                    </div>
                  </div>
                </UFormGroup>
              </div>

              <!-- Location Selection -->
              <div class="mb-6">
                <UFormGroup :label="isBatchMode ? '地点選択（複数選択可）' : '地点選択'" class="mb-4">
                  <!-- Single location mode -->
                  <USelectMenu
                    v-if="!isBatchMode"
                    v-model="selectedLocation"
                    :options="locations"
                    placeholder="地点を選択..."
                    :loading="locationsLoading"
                    searchable
                  />
                  
                  <!-- Batch mode -->
                  <div v-else class="space-y-3">
                    <!-- Quick select buttons -->
                    <div class="space-y-2">
                      <div class="flex flex-wrap gap-2">
                        <UButton 
                          @click="selectAllLocations"
                          size="xs" 
                          variant="outline"
                          icon="i-heroicons-check-circle"
                          color="green"
                        >
                          🌍 全地点選択
                        </UButton>
                        <UButton 
                          @click="clearAllLocations"
                          size="xs" 
                          variant="outline"
                          icon="i-heroicons-x-circle"
                          color="red"
                        >
                          クリア
                        </UButton>
                      </div>
                      
                      <div class="text-xs font-medium text-gray-700 mb-1">地域選択:</div>
                      <div class="flex flex-wrap gap-1">
                        <UButton 
                          v-for="region in ['北海道', '東北', '北陸', '関東', '甲信', '東海', '近畿', '中国', '四国', '九州', '沖縄']"
                          :key="region"
                          @click="selectRegionLocations(region)" 
                          size="xs" 
                          :variant="isRegionSelected(region) ? 'solid' : 'outline'"
                          :color="isRegionSelected(region) ? 'primary' : 'gray'"
                        >
                          {{ region }}
                        </UButton>
                      </div>
                    </div>
                    
                    <!-- Multiple select -->
                    <USelectMenu
                      v-model="selectedLocations"
                      :options="locations"
                      placeholder="地点を選択..."
                      :loading="locationsLoading"
                      multiple
                      searchable
                    />
                    
                    <!-- Selected count -->
                    <div class="text-sm text-gray-600">
                      選択中: {{ selectedLocations.length }}地点
                    </div>
                  </div>
                </UFormGroup>
              </div>

              <!-- LLM Provider Selection -->
              <div class="mb-6">
                <UFormGroup label="LLMプロバイダー" class="mb-4">
                  <USelectMenu
                    v-model="selectedProvider"
                    :options="providerOptions"
                    placeholder="プロバイダーを選択..."
                    :loading="providersLoading"
                  />
                </UFormGroup>
              </div>

              <!-- Forecast Hours Setting -->
              <div class="mb-6">
                <UFormGroup label="予報基準時間（時間後）" class="mb-4">
                  <UInput
                    v-model.number="forecastHours"
                    type="number"
                    min="1"
                    max="72"
                    placeholder="12"
                  />
                  <div class="text-xs text-gray-500 mt-1">
                    {{ forecastHours }}時間後を基準とした前後24時間の天気変化を分析
                  </div>
                  <div class="text-xs text-gray-400 mt-1">
                    • 実際の予報範囲: {{ Math.max(0, forecastHours - 12) }}〜{{ forecastHours + 12 }}時間後
                    <br>
                    • キャッシュがある場合: 前{{ forecastHours + 12 }}時間の変化も考慮
                  </div>
                </UFormGroup>
              </div>

              <!-- Current Time -->
              <div class="mb-6">
                <UAlert
                  color="blue"
                  variant="subtle"
                  :title="`生成時刻: ${currentTime}`"
                  icon="i-heroicons-clock"
                />
              </div>

              <!-- Generate Button -->
              <UButton
                @click="generateComment"
                :loading="generating"
                :disabled="(isBatchMode && selectedLocations.length === 0) || (!isBatchMode && !selectedLocation) || !selectedProvider || generating"
                color="primary"
                size="lg"
                block
              >
                <UIcon name="i-heroicons-sparkles" class="w-5 h-5 mr-2" />
                {{ isBatchMode ? '一括コメント生成' : 'コメント生成' }}
              </UButton>
            </UCard>

            <!-- History Panel -->
            <UCard class="mt-6">
              <template #header>
                <div class="flex items-center">
                  <UIcon name="i-heroicons-clock" class="w-5 h-5 mr-2" />
                  <h2 class="text-lg font-semibold">生成履歴</h2>
                </div>
              </template>
              
              <div v-if="history.length === 0" class="text-center text-gray-500 py-4">
                履歴がありません
              </div>
              
              <div v-else class="space-y-3 max-h-64 overflow-y-auto">
                <div
                  v-for="(item, index) in history.slice(0, 5)"
                  :key="index"
                  class="p-3 bg-gray-50 rounded-lg"
                >
                  <div class="text-sm font-medium text-gray-900">
                    {{ item.location || '不明な地点' }}
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    {{ formatDate(item.timestamp) }}
                  </div>
                  <div class="text-sm text-gray-700 mt-2 line-clamp-2">
                    {{ item.comment || item.final_comment || 'コメントなし' }}
                  </div>
                </div>
              </div>
            </UCard>
          </div>

          <!-- Right Panel: Results -->
          <div class="lg:col-span-2">
            <UCard>
              <template #header>
                <div class="flex items-center">
                  <UIcon name="i-heroicons-chat-bubble-left-ellipsis" class="w-5 h-5 mr-2" />
                  <h2 class="text-lg font-semibold">生成結果</h2>
                </div>
              </template>

              <!-- Loading State -->
              <div v-if="generating" class="text-center py-12">
                <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
                <div class="text-lg font-medium text-gray-900">生成中...</div>
                <div class="text-sm text-gray-500 mt-2">
                  {{ isBatchMode 
                    ? `${selectedLocations.length}地点のコメントを生成しています` 
                    : `${selectedLocation} のコメントを生成しています` }}
                </div>
              </div>

              <!-- Batch Results -->
              <div v-else-if="isBatchMode && results.length > 0" class="space-y-4">
                <div class="mb-4">
                  <h3 class="text-lg font-semibold">一括生成結果</h3>
                  <div class="text-sm text-gray-600">
                    成功: {{ results.filter(r => r.success).length }}件 / 
                    全体: {{ results.length }}件
                  </div>
                </div>
                
                <div v-for="(batchResult, index) in results" :key="index" class="border rounded-lg p-4">
                  <div v-if="batchResult.success">
                    <UAlert
                      color="green"
                      variant="subtle"
                      :title="`${batchResult.location} - 生成完了`"
                      icon="i-heroicons-check-circle"
                      class="mb-3"
                    />
                    <div class="p-3 bg-green-50 rounded border border-green-200">
                      <div class="font-medium text-green-900 mb-1">{{ batchResult.location }}:</div>
                      <div class="text-green-800">{{ batchResult.comment }}</div>
                    </div>
                  </div>
                  <div v-else>
                    <UAlert
                      color="red"
                      variant="subtle"
                      :title="`${batchResult.location} - 生成失敗`"
                      :description="batchResult.error"
                      icon="i-heroicons-exclamation-triangle"
                    />
                  </div>
                </div>
              </div>

              <!-- Single Result -->
              <div v-else-if="!isBatchMode && result" class="space-y-4">
                <!-- Success Result -->
                <div v-if="result.success" class="space-y-4">
                  <UAlert
                    color="green"
                    variant="subtle"
                    :title="`${result.location} のコメント生成が完了しました`"
                    icon="i-heroicons-check-circle"
                  />
                  
                  <div class="p-4 bg-green-50 rounded-lg border border-green-200">
                    <div class="text-lg font-medium text-green-900 mb-2">
                      生成されたコメント:
                    </div>
                    <div class="text-green-800">
                      {{ result.comment }}
                    </div>
                  </div>

                  <!-- Weather Details -->
                  <div v-if="result.metadata" class="mt-4">
                    <UAccordion 
                      :items="[{
                        label: '詳細情報',
                        icon: 'i-heroicons-information-circle',
                        slot: 'weather-details'
                      }]"
                    >
                      <template #weather-details>
                        <div class="p-4">
                          <div class="grid grid-cols-2 gap-4 mb-4">
                            <div v-if="result.metadata.temperature !== undefined">
                              <div class="text-sm font-medium text-gray-700">気温</div>
                              <div class="text-lg">{{ result.metadata.temperature }}°C</div>
                            </div>
                            <div v-if="result.metadata.weather_condition">
                              <div class="text-sm font-medium text-gray-700">天気</div>
                              <div class="text-lg">{{ result.metadata.weather_condition }}</div>
                            </div>
                            <div v-if="result.metadata.wind_speed !== undefined">
                              <div class="text-sm font-medium text-gray-700">風速</div>
                              <div class="text-lg">{{ result.metadata.wind_speed }}m/s</div>
                            </div>
                            <div v-if="result.metadata.humidity !== undefined">
                              <div class="text-sm font-medium text-gray-700">湿度</div>
                              <div class="text-lg">{{ result.metadata.humidity }}%</div>
                            </div>
                          </div>
                          
                          <div v-if="result.metadata.weather_forecast_time" class="p-3 bg-blue-50 rounded mb-4">
                            <div class="text-sm font-medium text-blue-700">予報基準時刻</div>
                            <div class="text-blue-600">{{ formatDateTime(result.metadata.weather_forecast_time) }}</div>
                            <div class="text-xs text-blue-500 mt-1">
                              この時刻を中心とした前後24時間の天気変化を分析してコメントを生成
                            </div>
                          </div>

                          <!-- Weather Timeline -->
                          <div v-if="result.metadata.weather_timeline" class="mb-4">
                            <div class="text-sm font-medium text-gray-700 mb-3">時系列予報データ</div>
                            
                            <!-- Summary -->
                            <div v-if="result.metadata.weather_timeline.summary" class="p-3 bg-gray-50 rounded mb-3">
                              <div class="text-xs font-medium text-gray-600 mb-1">概要</div>
                              <div class="text-sm text-gray-700">
                                {{ result.metadata.weather_timeline.summary.weather_pattern }} | 
                                気温範囲: {{ result.metadata.weather_timeline.summary.temperature_range }} | 
                                最大降水量: {{ result.metadata.weather_timeline.summary.max_precipitation }}
                              </div>
                            </div>

                            <!-- Past Forecasts -->
                            <div v-if="result.metadata.weather_timeline.past_forecasts && result.metadata.weather_timeline.past_forecasts.length > 0" class="mb-3">
                              <div class="text-xs font-medium text-gray-600 mb-2">過去の推移（12時間前〜基準時刻）</div>
                              <div class="grid grid-cols-1 gap-1">
                                <div v-for="forecast in result.metadata.weather_timeline.past_forecasts" :key="forecast.time" 
                                     class="flex justify-between items-center py-1 px-2 bg-orange-50 rounded text-xs">
                                  <span class="font-mono">{{ forecast.label }}</span>
                                  <span>{{ forecast.time }}</span>
                                  <span class="font-medium">{{ forecast.weather }}</span>
                                  <span>{{ forecast.temperature }}°C</span>
                                  <span v-if="forecast.precipitation > 0" class="text-blue-600">{{ forecast.precipitation }}mm</span>
                                </div>
                              </div>
                            </div>

                            <!-- Future Forecasts -->
                            <div v-if="result.metadata.weather_timeline.future_forecasts && result.metadata.weather_timeline.future_forecasts.length > 0">
                              <div class="text-xs font-medium text-gray-600 mb-2">今後の予報（3〜12時間後）</div>
                              <div class="grid grid-cols-1 gap-1">
                                <div v-for="forecast in result.metadata.weather_timeline.future_forecasts" :key="forecast.time" 
                                     class="flex justify-between items-center py-1 px-2 bg-green-50 rounded text-xs">
                                  <span class="font-mono">{{ forecast.label }}</span>
                                  <span>{{ forecast.time }}</span>
                                  <span class="font-medium">{{ forecast.weather }}</span>
                                  <span>{{ forecast.temperature }}°C</span>
                                  <span v-if="forecast.precipitation > 0" class="text-blue-600">{{ forecast.precipitation }}mm</span>
                                </div>
                              </div>
                            </div>

                            <!-- Error Display -->
                            <div v-if="result.metadata.weather_timeline.error" class="p-2 bg-red-50 rounded text-xs text-red-600">
                              時系列データ取得エラー: {{ result.metadata.weather_timeline.error }}
                            </div>
                          </div>

                          <!-- Selected Comments -->
                          <div v-if="result.metadata.selected_weather_comment || result.metadata.selected_advice_comment" class="border-t pt-4">
                            <div class="text-sm font-medium text-gray-700 mb-2">選択されたコメント:</div>
                            <div v-if="result.metadata.selected_weather_comment" class="text-sm text-gray-600 mb-1">
                              <strong>天気:</strong> {{ result.metadata.selected_weather_comment }}
                            </div>
                            <div v-if="result.metadata.selected_advice_comment" class="text-sm text-gray-600">
                              <strong>アドバイス:</strong> {{ result.metadata.selected_advice_comment }}
                            </div>
                          </div>
                        </div>
                      </template>
                    </UAccordion>
                  </div>
                </div>

                <!-- Error Result -->
                <div v-else class="space-y-4">
                  <UAlert
                    color="red"
                    variant="subtle"
                    :title="`${result.location} のコメント生成に失敗しました`"
                    :description="result.error"
                    icon="i-heroicons-exclamation-triangle"
                  />
                </div>
              </div>

              <!-- Initial State -->
              <div v-else class="text-center py-12">
                <UIcon name="i-heroicons-chat-bubble-left-ellipsis" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <div class="text-lg font-medium text-gray-900">コメント生成の準備完了</div>
                <div class="text-sm text-gray-500 mt-2">
                  左側のパネルから地点とプロバイダーを選択して、「コメント生成」ボタンをクリックしてください
                </div>
                
                <!-- Sample Comments -->
                <div class="mt-8 p-4 bg-gray-50 rounded-lg text-left">
                  <div class="text-sm font-medium text-gray-700 mb-4">サンプルコメント:</div>
                  <div class="space-y-2 text-sm text-gray-600">
                    <div><strong>晴れの日:</strong> 爽やかな朝ですね</div>
                    <div><strong>雨の日:</strong> 傘をお忘れなく</div>
                    <div><strong>曇りの日:</strong> 過ごしやすい一日です</div>
                    <div><strong>雪の日:</strong> 足元にお気をつけて</div>
                  </div>
                </div>
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { REGIONS, getAllLocations, getLocationsByRegion } from '~/constants/regions'

// Page meta
useHead({
  title: '天気コメント生成システム',
  meta: [
    { name: 'description', content: '天気に基づいたコメントを生成するシステム' }
  ]
})

// Reactive state
const selectedLocation = ref('')
const selectedLocations = ref([])
const selectedProvider = ref({ label: 'OpenAI GPT', value: 'openai' })
const generating = ref(false)
const result = ref(null)
const results = ref([])
const locations = ref([])
const providers = ref([])
const history = ref([])
const locationsLoading = ref(false)
const providersLoading = ref(false)
const forecastHours = ref(12)
const isBatchMode = ref(false)

// Computed properties
const currentTime = computed(() => {
  return new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const locationOptions = computed(() => 
  locations.value.map(location => ({
    label: location,
    value: location,
    id: location
  }))
)

const providerOptions = computed(() => 
  providers.value.map(provider => ({
    label: provider.name,
    value: provider.id
  }))
)

// API base URL
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// API functions
const fetchLocations = async () => {
  locationsLoading.value = true
  try {
    const response = await $fetch(`${apiBaseUrl}/api/locations`)
    locations.value = response.locations
  } catch (error) {
    console.error('Failed to fetch locations:', error)
    // Fallback to region-based data
    locations.value = getAllLocations()
    console.log('Using region-based location data:', locations.value.length, 'locations')
  } finally {
    locationsLoading.value = false
  }
}

const fetchProviders = async () => {
  providersLoading.value = true
  try {
    const response = await $fetch(`${apiBaseUrl}/api/providers`)
    providers.value = response.providers
  } catch (error) {
    console.error('Failed to fetch providers:', error)
    // Fallback to mock data
    providers.value = [
      { id: 'openai', name: 'OpenAI GPT', description: 'OpenAI\'s GPT models' },
      { id: 'gemini', name: 'Gemini', description: 'Google\'s Gemini AI' },
      { id: 'anthropic', name: 'Claude', description: 'Anthropic\'s Claude AI' }
    ]
  } finally {
    providersLoading.value = false
  }
}

const fetchHistory = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/api/history`)
    history.value = response.history || []
  } catch (error) {
    console.error('Failed to fetch history:', error)
    history.value = []
  }
}

const generateComment = async () => {
  // Determine locations to process
  const locationsToProcess = isBatchMode.value 
    ? selectedLocations.value 
    : selectedLocation.value ? [selectedLocation.value] : []

  const providerValue = selectedProvider.value?.value || selectedProvider.value
  if (locationsToProcess.length === 0 || !providerValue) {
    console.warn('Location or provider not selected:', { 
      locations: locationsToProcess, 
      provider: providerValue 
    })
    return
  }

  console.log('Starting comment generation:', { 
    locations: locationsToProcess, 
    provider: providerValue,
    forecastHours: forecastHours.value
  })
  
  generating.value = true
  result.value = null
  results.value = []

  try {
    if (isBatchMode.value) {
      // Batch generation
      const allResults = []
      
      for (const location of locationsToProcess) {
        const requestBody = {
          location: location,
          llm_provider: selectedProvider.value.value || selectedProvider.value,
          target_datetime: new Date().toISOString()
        }
        
        console.log('Request body for', location, ':', requestBody)
        
        try {
          const response = await $fetch(`${apiBaseUrl}/api/generate`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: requestBody
          })

          allResults.push(response)
        } catch (error) {
          allResults.push({
            success: false,
            location: location,
            error: error.message || 'コメント生成に失敗しました'
          })
        }
      }
      
      results.value = allResults
      console.log('Batch generation results:', allResults)
      
      // Refresh history
      await fetchHistory()
      
    } else {
      // Single location generation
      const requestBody = {
        location: locationsToProcess[0],
        llm_provider: selectedProvider.value.value || selectedProvider.value,
        target_datetime: new Date().toISOString()
      }
      
      console.log('Request body:', requestBody)
      
      const response = await $fetch(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: requestBody
      })

      console.log('Response received:', response)
      result.value = response
      
      // Refresh history if generation was successful
      if (response.success) {
        await fetchHistory()
      }
    }
  } catch (error) {
    console.error('Failed to generate comment:', error)
    
    // Check if it's a network error
    let errorMessage = 'コメント生成中にエラーが発生しました'
    if (error.message?.includes('fetch')) {
      errorMessage = 'APIサーバーに接続できません。サーバーが起動しているか確認してください。'
    } else if (error.data?.detail) {
      errorMessage = error.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    
    if (isBatchMode.value) {
      results.value = [{
        success: false,
        location: '一括生成',
        error: errorMessage
      }]
    } else {
      result.value = {
        success: false,
        location: locationsToProcess[0] || '不明な地点',
        error: errorMessage
      }
    }
  } finally {
    generating.value = false
  }
}

// Utility functions
const formatDate = (timestamp) => {
  if (!timestamp) return '不明'
  return new Date(timestamp).toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDateTime = (dateString) => {
  if (!dateString) return '不明'
  try {
    const date = new Date(dateString.replace('Z', '+00:00'))
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

// Location selection helpers
const selectAllLocations = () => {
  selectedLocations.value = [...locations.value]
}

const clearAllLocations = () => {
  selectedLocations.value = []
}

const selectRegionLocations = (regionName: string) => {
  const regionLocations = getLocationsByRegion(regionName)
  
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

const isRegionSelected = (regionName: string) => {
  const regionLocations = getLocationsByRegion(regionName)
  return regionLocations.length > 0 && regionLocations.every(loc => selectedLocations.value.includes(loc))
}

// Initialize on mount
onMounted(async () => {
  console.log('Component mounted, fetching initial data...')
  
  await Promise.all([
    fetchLocations(),
    fetchProviders(),
    fetchHistory()
  ])
  
  console.log('Initial data loaded:', { 
    locations: locations.value.length, 
    providers: providers.value.length, 
    history: history.value.length 
  })
  
  // Set default selections
  if (locations.value.length > 0) {
    selectedLocation.value = locations.value[0]
    console.log('Default location set:', selectedLocation.value)
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