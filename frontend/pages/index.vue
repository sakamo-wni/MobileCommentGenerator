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
            Version 1.0.1 <!-- Version Update -->
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
                           @click="toggleBatchMode">
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
                  <USelectMenu
                    v-if="!isBatchMode"
                    v-model="selectedLocation"
                    :options="locationsForSelect"
                    placeholder="地点を選択..."
                    :loading="locationsLoading"
                    searchable
                    value-attribute="id"
                    option-attribute="label"
                    class="w-full"
                  />
                  <div v-else class="space-y-3">
                    <div class="space-y-2">
                      <div class="flex flex-wrap gap-2">
                        <UButton @click="selectAllLocations" size="xs" variant="outline" icon="i-heroicons-check-circle" color="green">🌍 全地点選択</UButton>
                        <UButton @click="clearAllLocations" size="xs" variant="outline" icon="i-heroicons-x-circle" color="red">クリア</UButton>
                      </div>
                      <div class="text-xs font-medium text-gray-700 mb-1">地域選択:</div>
                      <div class="flex flex-wrap gap-1">
                        <UButton 
                          v-for="region in ['北海道', '東北', '北陸', '関東', '甲信', '東海', '近畿', '中国', '四国', '九州', '沖縄']"
                          :key="region" @click="selectRegionLocations(region)" size="xs"
                          :variant="isRegionSelected(region) ? 'solid' : 'outline'"
                          :color="isRegionSelected(region) ? 'primary' : 'gray'">{{ region }}</UButton>
                      </div>
                    </div>
                    <USelectMenu
                      v-model="selectedLocations"
                      :options="locationsForSelect"
                      placeholder="地点を選択..."
                      :loading="locationsLoading"
                      multiple
                      searchable
                      value-attribute="id"
                      option-attribute="label"
                      class="w-full"
                    />
                    <div class="text-sm text-gray-600">選択中: {{ selectedLocations.length }}地点</div>
                  </div>
                </UFormGroup>
              </div>

              <!-- LLM Provider Selection -->
              <div class="mb-6">
                <UFormGroup label="LLMプロバイダー" class="mb-4">
                  <USelectMenu
                    v-model="selectedProviderValue"
                    :options="providerOptions"
                    placeholder="プロバイダーを選択..."
                    :loading="providersLoading"
                    value-attribute="value"
                    option-attribute="label"
                    class="w-full"
                  />
                </UFormGroup>
              </div>

              <div class="mb-6">
                <UAlert color="blue" variant="subtle" title="天気予報の仕様" icon="i-heroicons-cloud">
                  <template #description><div class="text-sm space-y-1"><div>• 予報時刻: 翌日の9:00, 12:00, 15:00, 18:00（JST）</div><div>• 優先順位: 雷・嵐 > 本降りの雨 > 猛暑日熱中症対策 > 雨 > 曇り > 晴れ</div></div></template>
                </UAlert>
              </div>
              <div class="mb-6">
                <UAlert color="blue" variant="subtle" :title="`生成時刻: ${currentTime}`" icon="i-heroicons-clock"/>
              </div>

              <UButton
                @click="generateComment"
                :loading="generating"
                :disabled="(isBatchMode && selectedLocations.length === 0) || (!isBatchMode && !selectedLocation) || !selectedProviderValue || generating"
                color="primary" size="lg" block>
                <UIcon name="i-heroicons-sparkles" class="w-5 h-5 mr-2" />
                {{ isBatchMode ? '一括コメント生成' : 'コメント生成' }}
              </UButton>
            </UCard>

            <UCard class="mt-6">
              <template #header><div class="flex items-center"><UIcon name="i-heroicons-clock" class="w-5 h-5 mr-2" /><h2 class="text-lg font-semibold">生成履歴</h2></div></template>
              <div v-if="history.length === 0" class="text-center text-gray-500 py-4">履歴がありません</div>
              <div v-else class="space-y-3 max-h-64 overflow-y-auto">
                <div v-for="(item, index) in history.slice(0, 5)" :key="index" class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-sm font-medium text-gray-900">{{ item.location || '不明な地点' }}</div>
                  <div class="text-xs text-gray-500 mt-1">{{ formatDate(item.timestamp) }}</div>
                  <div class="text-sm text-gray-700 mt-2 line-clamp-2">{{ item.comment || item.final_comment || 'コメントなし' }}</div>
                </div>
              </div>
            </UCard>
          </div>

          <div class="lg:col-span-2">
            <UCard>
              <template #header><div class="flex items-center"><UIcon name="i-heroicons-chat-bubble-left-ellipsis" class="w-5 h-5 mr-2" /><h2 class="text-lg font-semibold">生成結果</h2></div></template>

              <div v-if="generating && shouldShowOverallLoading" class="text-center py-12">
                <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
                <div class="text-lg font-medium text-gray-900">{{ overallLoadingStatusText }}</div>
              </div>

              <div v-else-if="isBatchMode && results.length > 0" class="space-y-4">
                <div class="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 class="text-lg font-semibold text-blue-800">一括生成サマリー</h3>
                  <div class="text-sm text-blue-700 mt-1">
                    処理完了: {{ results.filter(r => r.status === 'success' || r.status === 'error').length }} / {{ results.length }} 地点
                  </div>
                  <div class="text-sm text-green-700">
                    成功: {{ results.filter(r => r.status === 'success').length }} 件
                  </div>
                   <div v-if="batchErrors.length > 0" class="text-sm text-red-700">
                    失敗: {{ batchErrors.length }} 件
                  </div>
                  <div v-if="results.length > 0" class="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mt-2">
                    <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out" :style="{ width: `${(results.filter(r => r.status === 'success' || r.status === 'error').length / results.length) * 100}%` }"></div>
                  </div>
                </div>

                <div v-if="batchErrors.length > 0 && !generating" class="mt-4 p-4 border border-red-300 bg-red-50 rounded-lg">
                  <h4 class="text-md font-semibold text-red-700 mb-2 flex items-center">
                    <UIcon name="i-heroicons-exclamation-triangle" class="w-5 h-5 mr-2"/>
                    エラーが発生した地点:
                  </h4>
                  <ul class="list-disc list-inside space-y-1 pl-5">
                    <li v-for="(errorItem, index) in batchErrors" :key="'err-' + errorItem.location + '-' + index" class="text-sm text-red-600">
                      <strong>{{ errorItem.location }}:</strong> {{ errorItem.error }}
                    </li>
                  </ul>
                </div>

                <div v-for="(batchItem, index) in results" :key="batchItem.location + '-' + index" class="border rounded-lg p-4 shadow-sm">
                  <div v-if="batchItem.status === 'pending'" class="flex items-center text-gray-500"><UIcon name="i-heroicons-clock" class="w-5 h-5 mr-2" /><span>{{ batchItem.location }} - 生成待機中...</span></div>
                  <div v-else-if="batchItem.status === 'generating'" class="flex items-center text-blue-500"><UIcon name="i-heroicons-arrow-path" class="w-5 h-5 mr-2 animate-spin" /><span>{{ batchItem.location }} - 生成中...</span></div>
                  <div v-else-if="batchItem.status === 'success' && batchItem.success">
                    <UAlert color="green" variant="subtle" :title="`${batchItem.location} - 生成完了`" icon="i-heroicons-check-circle" class="mb-3"/>
                    <div class="p-3 bg-green-50 rounded border border-green-200 mb-3"><div class="font-medium text-green-900 mb-1">{{ batchItem.location }}:</div><div class="text-green-800">{{ batchItem.comment }}</div></div>
                    <div v-if="batchItem.metadata" class="mt-3">
                      <UAccordion :items="[{label: `${batchItem.location} の詳細情報`, icon: 'i-heroicons-information-circle', slot: `weather-details-batch-${index}`}]">
                        <template #[`weather-details-batch-${index}`]><div class="p-4">
                          <div class="grid grid-cols-2 gap-4 mb-4">
                            <div v-if="batchItem.metadata.temperature !== undefined"><div class="text-sm font-medium text-gray-700">気温</div><div class="text-lg">{{ batchItem.metadata.temperature }}°C</div></div>
                            <div v-if="batchItem.metadata.weather_condition"><div class="text-sm font-medium text-gray-700">天気</div><div class="text-lg">{{ batchItem.metadata.weather_condition }}</div></div>
                            <div v-if="batchItem.metadata.wind_speed !== undefined"><div class="text-sm font-medium text-gray-700">風速</div><div class="text-lg">{{ batchItem.metadata.wind_speed }}m/s</div></div>
                            <div v-if="batchItem.metadata.humidity !== undefined"><div class="text-sm font-medium text-gray-700">湿度</div><div class="text-lg">{{ batchItem.metadata.humidity }}%</div></div>
                          </div>
                          <div v-if="batchItem.metadata.weather_forecast_time" class="p-3 bg-blue-50 rounded mb-4"><div class="text-sm font-medium text-blue-700">予報基準時刻</div><div class="text-blue-600">{{ formatDateTime(batchItem.metadata.weather_forecast_time) }}</div></div>
                          <div v-if="batchItem.metadata.weather_timeline" class="mb-4">
                             <div class="text-sm font-medium text-gray-700 mb-3">時系列予報データ</div>
                             <div v-if="batchItem.metadata.weather_timeline.summary" class="p-3 bg-gray-50 rounded mb-3"><div class="text-xs font-medium text-gray-600 mb-1">概要</div><div class="text-sm text-gray-700">{{ batchItem.metadata.weather_timeline.summary.weather_pattern }} | 気温範囲: {{ batchItem.metadata.weather_timeline.summary.temperature_range }} | 最大降水量: {{ batchItem.metadata.weather_timeline.summary.max_precipitation }}</div></div>
                             <div v-if="batchItem.metadata.weather_timeline.past_forecasts && batchItem.metadata.weather_timeline.past_forecasts.length > 0" class="mb-3">
                               <div class="text-xs font-medium text-gray-600 mb-2">過去の推移</div><div class="grid grid-cols-1 gap-1"><div v-for="fc in batchItem.metadata.weather_timeline.past_forecasts" :key="fc.time" class="flex justify-between items-center py-1 px-2 bg-orange-50 rounded text-xs"><span class="font-mono">{{ fc.label }}</span><span>{{ fc.time }}</span><span class="font-medium">{{ fc.weather }}</span><span>{{ fc.temperature }}°C</span><span v-if="fc.precipitation > 0" class="text-blue-600">{{ fc.precipitation }}mm</span></div></div></div>
                             <div v-if="batchItem.metadata.weather_timeline.future_forecasts && batchItem.metadata.weather_timeline.future_forecasts.length > 0">
                               <div class="text-xs font-medium text-gray-600 mb-2">今後の予報</div><div class="grid grid-cols-1 gap-1"><div v-for="fc in batchItem.metadata.weather_timeline.future_forecasts" :key="fc.time" class="flex justify-between items-center py-1 px-2 bg-green-50 rounded text-xs"><span class="font-mono">{{ fc.label }}</span><span>{{ fc.time }}</span><span class="font-medium">{{ fc.weather }}</span><span>{{ fc.temperature }}°C</span><span v-if="fc.precipitation > 0" class="text-blue-600">{{ fc.precipitation }}mm</span></div></div></div>
                             <div v-if="batchItem.metadata.weather_timeline.error" class="p-2 bg-red-50 rounded text-xs text-red-600">時系列データ取得エラー: {{ batchItem.metadata.weather_timeline.error }}</div>
                          </div>
                          <div v-if="batchItem.metadata.selected_weather_comment || batchItem.metadata.selected_advice_comment" class="border-t pt-4"><div class="text-sm font-medium text-gray-700 mb-2">選択されたコメント:</div><div v-if="batchItem.metadata.selected_weather_comment" class="text-sm text-gray-600 mb-1"><strong>天気:</strong> {{ batchItem.metadata.selected_weather_comment }}</div><div v-if="batchItem.metadata.selected_advice_comment" class="text-sm text-gray-600"><strong>アドバイス:</strong> {{ batchItem.metadata.selected_advice_comment }}</div></div>
                        </div></template>
                      </UAccordion>
                    </div>
                  </div>
                  <div v-else-if="batchItem.status === 'error' || !batchItem.success"> {/* Catches both explicit error status and success:false */}
                    <UAlert color="red" variant="subtle" :title="`${batchItem.location} - 生成失敗`" :description="batchItem.error" icon="i-heroicons-exclamation-triangle"/>
                  </div>
                </div>
              </div>

              <div v-else-if="!isBatchMode && result" class="space-y-4">
                <div v-if="result.success" class="space-y-4">
                  <UAlert color="green" variant="subtle" :title="`${result.location} のコメント生成が完了しました`" icon="i-heroicons-check-circle"/>
                  <div class="p-4 bg-green-50 rounded-lg border border-green-200"><div class="text-lg font-medium text-green-900 mb-2">生成されたコメント:</div><div class="text-green-800">{{ result.comment }}</div></div>
                  <div v-if="result.metadata" class="mt-4">
                    <UAccordion :items="[{label: '詳細情報', icon: 'i-heroicons-information-circle', slot: 'weather-details-single'}]">
                      <template #weather-details-single><div class="p-4">
                        <div class="grid grid-cols-2 gap-4 mb-4">
                          <div v-if="result.metadata.temperature !== undefined"><div class="text-sm font-medium text-gray-700">気温</div><div class="text-lg">{{ result.metadata.temperature }}°C</div></div>
                          <div v-if="result.metadata.weather_condition"><div class="text-sm font-medium text-gray-700">天気</div><div class="text-lg">{{ result.metadata.weather_condition }}</div></div>
                          <div v-if="result.metadata.wind_speed !== undefined"><div class="text-sm font-medium text-gray-700">風速</div><div class="text-lg">{{ result.metadata.wind_speed }}m/s</div></div>
                          <div v-if="result.metadata.humidity !== undefined"><div class="text-sm font-medium text-gray-700">湿度</div><div class="text-lg">{{ result.metadata.humidity }}%</div></div>
                        </div>
                        <div v-if="result.metadata.weather_forecast_time" class="p-3 bg-blue-50 rounded mb-4"><div class="text-sm font-medium text-blue-700">予報基準時刻</div><div class="text-blue-600">{{ formatDateTime(result.metadata.weather_forecast_time) }}</div></div>
                        <div v-if="result.metadata.weather_timeline" class="mb-4">
                           <div class="text-sm font-medium text-gray-700 mb-3">時系列予報データ</div>
                           <div v-if="result.metadata.weather_timeline.summary" class="p-3 bg-gray-50 rounded mb-3"><div class="text-xs font-medium text-gray-600 mb-1">概要</div><div class="text-sm text-gray-700">{{ result.metadata.weather_timeline.summary.weather_pattern }} | 気温範囲: {{ result.metadata.weather_timeline.summary.temperature_range }} | 最大降水量: {{ result.metadata.weather_timeline.summary.max_precipitation }}</div></div>
                           <div v-if="result.metadata.weather_timeline.past_forecasts && result.metadata.weather_timeline.past_forecasts.length > 0" class="mb-3">
                             <div class="text-xs font-medium text-gray-600 mb-2">過去の推移</div><div class="grid grid-cols-1 gap-1"><div v-for="fc in result.metadata.weather_timeline.past_forecasts" :key="fc.time" class="flex justify-between items-center py-1 px-2 bg-orange-50 rounded text-xs"><span class="font-mono">{{ fc.label }}</span><span>{{ fc.time }}</span><span class="font-medium">{{ fc.weather }}</span><span>{{ fc.temperature }}°C</span><span v-if="fc.precipitation > 0" class="text-blue-600">{{ fc.precipitation }}mm</span></div></div></div>
                           <div v-if="result.metadata.weather_timeline.future_forecasts && result.metadata.weather_timeline.future_forecasts.length > 0">
                             <div class="text-xs font-medium text-gray-600 mb-2">今後の予報</div><div class="grid grid-cols-1 gap-1"><div v-for="fc in result.metadata.weather_timeline.future_forecasts" :key="fc.time" class="flex justify-between items-center py-1 px-2 bg-green-50 rounded text-xs"><span class="font-mono">{{ fc.label }}</span><span>{{ fc.time }}</span><span class="font-medium">{{ fc.weather }}</span><span>{{ fc.temperature }}°C</span><span v-if="fc.precipitation > 0" class="text-blue-600">{{ fc.precipitation }}mm</span></div></div></div>
                           <div v-if="result.metadata.weather_timeline.error" class="p-2 bg-red-50 rounded text-xs text-red-600">時系列データ取得エラー: {{ result.metadata.weather_timeline.error }}</div>
                        </div>
                        <div v-if="result.metadata.selected_weather_comment || result.metadata.selected_advice_comment" class="border-t pt-4"><div class="text-sm font-medium text-gray-700 mb-2">選択されたコメント:</div><div v-if="result.metadata.selected_weather_comment" class="text-sm text-gray-600 mb-1"><strong>天気:</strong> {{ result.metadata.selected_weather_comment }}</div><div v-if="result.metadata.selected_advice_comment" class="text-sm text-gray-600"><strong>アドバイス:</strong> {{ result.metadata.selected_advice_comment }}</div></div>
                      </div></template>
                    </UAccordion>
                  </div>
                </div>
                <div v-else class="space-y-4"> {/* Handles single generation error */}
                  <UAlert color="red" variant="subtle" :title="`${result.location || '選択された地点'} のコメント生成に失敗しました`" :description="result.error" icon="i-heroicons-exclamation-triangle"/>
                </div>
              </div>

              <div v-else-if="!generating" class="text-center py-12">
                <UIcon name="i-heroicons-chat-bubble-left-ellipsis" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <div class="text-lg font-medium text-gray-900">コメント生成の準備完了</div>
                <div class="text-sm text-gray-500 mt-2">左側のパネルから地点とプロバイダーを選択して、「コメント生成」ボタンをクリックしてください</div>
                <div class="mt-8 p-4 bg-gray-50 rounded-lg text-left"><div class="text-sm font-medium text-gray-700 mb-4">サンプルコメント:</div><div class="space-y-2 text-sm text-gray-600"><div><strong>晴れの日:</strong> 爽やかな朝ですね</div><div><strong>雨の日:</strong> 傘をお忘れなく</div><div><strong>曇りの日:</strong> 過ごしやすい一日です</div><div><strong>雪の日:</strong> 足元にお気をつけて</div></div></div>
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { REGIONS, getAllLocations, getLocationsByRegion, getLocationOrder } from '~/constants/regions'

const devLog = (...args: any[]) => {
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.log(...args)
  }
}

const locationOrderMap = new Map(getLocationOrder().map((loc, idx) => [loc, idx]))

useHead({ title: '天気コメント生成システム', meta: [{ name: 'description', content: '天気に基づいたコメントを生成するシステム' }]})

// --- Reactive State ---
const selectedLocation = ref<string>('')
const selectedLocations = ref<string[]>([])
const selectedProviderValue = ref<string | undefined>() // Stores the provider's ID (value for USelectMenu)

const generating = ref(false)
const result = ref<any>(null)

interface BatchResult {
  location: string;
  success?: boolean;
  comment?: string;
  error?: string;
  metadata?: any;
  status: 'pending' | 'generating' | 'success' | 'error';
}
const results = ref<BatchResult[]>([])

const allRawLocations = ref<string[]>([])
const locationsLoading = ref(false)

const providers = ref<Array<{ id: string; name: string; description: string }>>([])
const providersLoading = ref(false)

const history = ref<any[]>([])
const isBatchMode = ref(false)

// --- Computed Properties ---
const currentTime = computed(() => new Date().toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }))

const locationsForSelect = computed(() =>
  allRawLocations.value.map(loc => ({ label: loc, id: loc }))
)

const providerOptions = computed(() => 
  providers.value.map(p => ({ label: p.name, value: p.id }))
)

const overallLoadingStatusText = computed(() => {
  if (!generating.value) return '';
  if (isBatchMode.value) {
    const total = selectedLocations.value.length; // Use selectedLocations for total
    const done = results.value.filter(r => r.status === 'success' || r.status === 'error').length;
    if (total === 0 && generating.value) return `コメント生成を準備中...`;
    return `一括生成中... (${done}/${total > 0 ? total : results.value.length} 地点完了)`;
  }
  return `${selectedLocation.value || '選択された地点'} のコメントを生成しています...`;
});

const shouldShowOverallLoading = computed(() => {
  if (!generating.value) return false;
  if (isBatchMode.value) {
    return results.value.length === 0 || results.value.every(r => r.status === 'pending');
  }
  return true;
});

const batchErrors = computed(() => {
  if (isBatchMode.value) {
    return results.value.filter(r => r.status === 'error' && r.error).map(r => ({location: r.location, error: r.error as string}));
  }
  return [];
});

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// --- API Functions ---
const fetchLocations = async () => {
  locationsLoading.value = true
  try {
    const response = await $fetch<{ locations: string[] }>(`${apiBaseUrl}/api/locations`)
    allRawLocations.value = response.locations || []
    if (allRawLocations.value.length > 0 && !isBatchMode.value && !selectedLocation.value) {
      selectedLocation.value = allRawLocations.value[0];
    }
  } catch (error) {
    console.error('Failed to fetch locations:', error)
    allRawLocations.value = getAllLocations()
    if (allRawLocations.value.length > 0 && !isBatchMode.value && !selectedLocation.value) {
      selectedLocation.value = allRawLocations.value[0];
    }
  } finally {
    locationsLoading.value = false
  }
}

const fetchProviders = async () => {
  providersLoading.value = true
  try {
    const response = await $fetch<{ providers: Array<{ id: string; name: string; description: string }> }>(`${apiBaseUrl}/api/providers`)
    providers.value = response.providers || []
    if (providers.value.length > 0 && !selectedProviderValue.value) {
      selectedProviderValue.value = providers.value[0].id;
    }
  } catch (error) {
    console.error('Failed to fetch providers:', error)
    providers.value = [
      { id: 'gemini', name: 'Gemini', description: 'Google\'s Gemini AI' },
      { id: 'openai', name: 'OpenAI GPT', description: 'OpenAI\'s GPT models' },
      { id: 'anthropic', name: 'Claude', description: 'Anthropic\'s Claude AI' }
    ]
    if (providers.value.length > 0 && !selectedProviderValue.value) {
      selectedProviderValue.value = providers.value[0].id;
    }
  } finally {
    providersLoading.value = false
  }
}

const fetchHistory = async () => {
  try {
    const response = await $fetch<{ history: any[] }>(`${apiBaseUrl}/api/history`)
    history.value = response.history || []
  } catch (error) { console.error('Failed to fetch history:', error); history.value = [] }
}

// --- Mode Toggle ---
const toggleBatchMode = () => {
  isBatchMode.value = !isBatchMode.value;
};

// --- Core Logic: Comment Generation ---
const generateComment = async () => {
  const locationsToProcessArray: string[] = isBatchMode.value
    ? selectedLocations.value
    : (selectedLocation.value ? [selectedLocation.value] : [])

  const sortedLocationsToProcess = [...locationsToProcessArray].sort(
    (a, b) => (locationOrderMap.get(a) ?? Infinity) - (locationOrderMap.get(b) ?? Infinity)
  )

  const providerId = selectedProviderValue.value;
  if (sortedLocationsToProcess.length === 0 || !providerId) {
    console.warn('Locations or provider not selected.')
    return
  }

  generating.value = true
  result.value = null

  if (isBatchMode.value) {
    results.value = sortedLocationsToProcess.map(locName => ({
      location: locName,
      status: 'pending',
    }))
  }

  try {
    if (isBatchMode.value) {
      await Promise.all(sortedLocationsToProcess.map(async (locationName) => {
        const resultIndex = results.value.findIndex(r => r.location === locationName)

        if (resultIndex !== -1 && results.value[resultIndex]) {
          results.value[resultIndex].status = 'generating'
        }

        const requestBody = {
          location: locationName,
          llm_provider: providerId,
          target_datetime: new Date().toISOString()
        }

        try {
          const response: any = await $fetch(`${apiBaseUrl}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: requestBody
          })

          if (resultIndex !== -1 && results.value[resultIndex]) {
            results.value[resultIndex] = {
              ...results.value[resultIndex],
              success: response.success,
              comment: response.comment,
              error: response.error,
              metadata: response.metadata,
              status: response.success ? 'success' : 'error',
            }
          }
        } catch (err: any) {
          if (resultIndex !== -1 && results.value[resultIndex]) {
            results.value[resultIndex].success = false
            results.value[resultIndex].error = err.data?.error || err.data?.detail || err.message || 'コメント生成に失敗しました'
            results.value[resultIndex].status = 'error'
          }
        }
        await nextTick()
      }))
      await fetchHistory()

    } else {
      const locationName = sortedLocationsToProcess[0]
      const requestBody = {
        location: locationName,
        llm_provider: providerId,
        target_datetime: new Date().toISOString()
      }
      const response = await $fetch<any>(`${apiBaseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: requestBody
      })
      result.value = response
      if (result.value.success) {
        await fetchHistory()
      }
    }
  } catch (error: any) {
    console.error('Overall error during comment generation process:', error)
    let errorMessage = 'コメント生成処理中に予期せぬエラーが発生しました。'
    if (error.message?.includes('fetch')) {
      errorMessage = 'APIサーバーに接続できません。サーバーが起動しているか確認してください。'
    } else if (error.data?.detail || error.data?.error) {
      errorMessage = error.data.detail || error.data.error
    } else if (error.message) {
      errorMessage = error.message
    }

    if (isBatchMode.value) {
      if (results.value.length === 0 || results.value.every(r => r.status === 'pending')) {
         results.value = [{ location: '一括処理全体', success: false, error: errorMessage, status: 'error' }];
      }
    } else {
      result.value = {
        success: false,
        location: sortedLocationsToProcess[0] || '不明な地点',
        error: errorMessage
      }
    }
  } finally {
    generating.value = false
  }
}

// --- Utility Functions ---
const formatDate = (timestamp: string | number | Date) => {
  if (!timestamp) return '不明';
  return new Date(timestamp).toLocaleString('ja-JP', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
const formatDateTime = (dateString: string) => {
  if (!dateString) return '不明';
  try {
    const d = new Date(dateString.replace('Z', '+00:00'));
    return d.toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return dateString
  }
}

// --- Location Selection Helpers ---
const selectAllLocations = () => { selectedLocations.value = [...allRawLocations.value] }
const clearAllLocations = () => { selectedLocations.value = [] }

const selectRegionLocations = (regionName: string) => {
  const regionLocations = getLocationsByRegion(regionName)
  const allCurrentlySelectedInRegion = regionLocations.length > 0 && regionLocations.every(loc => selectedLocations.value.includes(loc))
  
  if (allCurrentlySelectedInRegion) {
    selectedLocations.value = selectedLocations.value.filter(loc => !regionLocations.includes(loc))
  } else {
    const newLocationsToAdd = regionLocations.filter(loc => !selectedLocations.value.includes(loc))
    selectedLocations.value = [...new Set([...selectedLocations.value, ...newLocationsToAdd])]
  }
}
const isRegionSelected = (regionName: string) => {
  const regionLocations = getLocationsByRegion(regionName)
  if (regionLocations.length === 0) return false;
  return regionLocations.every(loc => selectedLocations.value.includes(loc))
}

// --- Lifecycle Hooks ---
onMounted(async () => {
  devLog('Component mounted, fetching initial data...')
  await Promise.all([fetchLocations(), fetchProviders(), fetchHistory()])
  devLog('Initial data loaded.')
})

watch(isBatchMode, (newVal, oldVal) => {
  if (newVal === oldVal) return;
  
  result.value = null;
  results.value = [];
  
  if (!newVal) {
    selectedLocations.value = [];
    if (allRawLocations.value.length > 0) {
      selectedLocation.value = allRawLocations.value[0];
    } else {
      selectedLocation.value = '';
    }
  } else {
    selectedLocation.value = '';
  }
}, { immediate: false });
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>