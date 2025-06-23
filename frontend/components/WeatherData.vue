<template>
  <AppCard>
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <Icon name="heroicons:cloud-sun" class="w-5 h-5 mr-2" />
          <h2 class="text-lg font-semibold">天気予報データ</h2>
        </div>
        
        <!-- Batch Mode Location Selector -->
        <div v-if="isBatchMode && batchResults && batchResults.length > 1" class="flex items-center space-x-2">
          <span class="text-sm text-gray-600">地点:</span>
          <select 
            :value="selectedIndex"
            @change="emit('update:selectedIndex', Number(($event.target as HTMLSelectElement).value))"
            class="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option 
              v-for="(result, index) in batchResults" 
              :key="index"
              :value="index"
            >
              {{ result.location }}
            </option>
          </select>
        </div>
      </div>
    </template>

    <div v-if="weatherData && weatherData.metadata" class="space-y-6">
      <!-- Current Weather -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold text-gray-800">現在の天気状況</h3>
          <div class="text-sm text-gray-600">
            {{ formatDateTime(weatherData.metadata.weather_forecast_time) }}
          </div>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-sm text-gray-600">天気</div>
            <div class="text-xl font-bold text-blue-600">{{ weatherData.metadata.weather_condition }}</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-600">気温</div>
            <div class="text-xl font-bold text-red-600">{{ weatherData.metadata.temperature }}°C</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-600">湿度</div>
            <div class="text-xl font-bold text-green-600">{{ weatherData.metadata.humidity }}%</div>
          </div>
          <div class="text-center">
            <div class="text-sm text-gray-600">風速</div>
            <div class="text-xl font-bold text-purple-600">{{ weatherData.metadata.wind_speed }}m/s</div>
          </div>
        </div>
      </div>

      <!-- Weather Timeline -->
      <div v-if="weatherData.metadata.weather_timeline" class="space-y-4">
        <h3 class="text-lg font-semibold text-gray-800">翌日の詳細予報</h3>
        
        <!-- Summary -->
        <div v-if="weatherData.metadata.weather_timeline.summary" class="bg-gray-50 p-4 rounded-lg">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span class="text-gray-600">気温範囲:</span>
              <span class="ml-2 font-medium">{{ weatherData.metadata.weather_timeline.summary.temperature_range }}</span>
            </div>
            <div>
              <span class="text-gray-600">最大降水量:</span>
              <span class="ml-2 font-medium">{{ weatherData.metadata.weather_timeline.summary.max_precipitation }}</span>
            </div>
            <div>
              <span class="text-gray-600">天気パターン:</span>
              <span class="ml-2 font-medium">{{ weatherData.metadata.weather_timeline.summary.weather_pattern }}</span>
            </div>
          </div>
        </div>

        <!-- Future Forecasts -->
        <div v-if="weatherData.metadata.weather_timeline.future_forecasts && weatherData.metadata.weather_timeline.future_forecasts.length > 0">
          <h4 class="text-md font-medium text-gray-700 mb-3">翌日（{{ getDateFromForecast(weatherData.metadata.weather_timeline.future_forecasts[0]) }}）の予報</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div 
              v-for="forecast in weatherData.metadata.weather_timeline.future_forecasts" 
              :key="forecast.time"
              class="bg-white border border-gray-200 rounded-lg p-3 shadow-sm"
            >
              <div class="text-center">
                <div class="text-sm font-medium text-gray-800">{{ forecast.label }}</div>
                <div class="text-lg font-bold text-blue-600 my-1">{{ forecast.weather }}</div>
                <div class="text-md font-semibold text-red-600">{{ forecast.temperature }}°C</div>
                <div v-if="forecast.precipitation > 0" class="text-sm text-blue-500 mt-1">
                  降水量: {{ forecast.precipitation }}mm
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Past Forecasts (if available) -->
        <div v-if="weatherData.metadata.weather_timeline.past_forecasts && weatherData.metadata.weather_timeline.past_forecasts.length > 0">
          <h4 class="text-md font-medium text-gray-700 mb-3">過去の実況</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div 
              v-for="past in weatherData.metadata.weather_timeline.past_forecasts" 
              :key="past.time"
              class="bg-gray-50 border border-gray-200 rounded-lg p-3"
            >
              <div class="text-center">
                <div class="text-sm font-medium text-gray-600">{{ past.label }}</div>
                <div class="text-lg font-bold text-gray-700 my-1">{{ past.weather }}</div>
                <div class="text-md font-semibold text-gray-600">{{ past.temperature }}°C</div>
                <div v-if="past.precipitation > 0" class="text-sm text-gray-500 mt-1">
                  降水量: {{ past.precipitation }}mm
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="text-center py-12">
      <Icon name="heroicons:cloud" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <div class="text-lg font-medium text-gray-900">天気データなし</div>
      <div class="text-sm text-gray-500 mt-2">
        コメントを生成すると、詳細な天気予報データが表示されます
      </div>
    </div>
  </AppCard>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { CommentGenerationResult, WeatherForecast } from '~/types'

interface Props {
  weatherData?: CommentGenerationResult | null
  isBatchMode?: boolean
  batchResults?: CommentGenerationResult[]
  selectedIndex?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:selectedIndex': [value: number]
}>()

const formatDateTime = (dateString: string) => {
  if (!dateString) return '不明'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

const getDateFromForecast = (forecast: WeatherForecast) => {
  if (!forecast || !forecast.time) return ''
  try {
    // "06/24 09:00" format
    const [date] = forecast.time.split(' ')
    return date
  } catch (error) {
    return ''
  }
}
</script>

<style scoped>
.weather-data {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.component-header {
  background: linear-gradient(135deg, #0C419A 0%, #6BA2FC 100%);
  color: white;
  padding: 1.5rem 2rem;
  border-bottom: 3px solid #6BA2FC;
}

.component-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.weather-content {
  padding: 2rem;
}
</style>