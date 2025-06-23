<template>
  <AppCard>
    <template #header>
      <div class="flex items-center">
        <Icon name="heroicons:chat-bubble-left-ellipsis" class="w-5 h-5 mr-2" />
        <h2 class="text-lg font-semibold">生成結果</h2>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="generating" class="text-center py-12">
      <Icon name="heroicons:arrow-path" class="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
      <div class="text-lg font-medium text-gray-900">生成中...</div>
      <div class="text-sm text-gray-500 mt-2">
        {{ isBatchMode 
          ? `${results.length}件の地点を処理中...` 
          : 'コメントを生成しています...' 
        }}
      </div>
    </div>

    <!-- Batch Results -->
    <div v-else-if="isBatchMode && results.length > 0" class="space-y-4">
      <div class="text-sm text-gray-600 mb-4">
        一括生成結果: {{ results.length }}件
      </div>
      
      <div v-for="(batchResult, index) in results" :key="index" class="border rounded-lg p-4">
        <div v-if="batchResult.success">
          <AppAlert
            color="green"
            :title="`${batchResult.location} - 生成完了`"
            icon="heroicons:check-circle"
          />
          
          <div class="mt-4 space-y-3">
            <div class="bg-gray-50 p-4 rounded-lg">
              <div class="text-sm font-medium text-gray-700 mb-2">生成されたコメント:</div>
              <div class="text-gray-900">{{ batchResult.comment }}</div>
            </div>
            
            <div v-if="batchResult.metadata" class="text-xs text-gray-500 space-y-1">
              <div><strong>天気:</strong> {{ batchResult.metadata.weather_condition }}</div>
              <div><strong>気温:</strong> {{ batchResult.metadata.temperature }}°C</div>
              <div><strong>生成時刻:</strong> {{ formatDateTime(batchResult.metadata.generated_at) }}</div>
            </div>
          </div>
        </div>
        <div v-else>
          <AppAlert
            color="red"
            :title="`${batchResult.location} - 生成失敗`"
            :description="batchResult.error"
            icon="heroicons:exclamation-triangle"
          />
        </div>
      </div>
    </div>

    <!-- Single Result -->
    <div v-else-if="!isBatchMode && result" class="space-y-4">
      <!-- Success Result -->
      <div v-if="result.success" class="space-y-4">
        <AppAlert
          color="green"
          :title="`${result.location} のコメント生成が完了しました`"
          icon="heroicons:check-circle"
        />
        
        <div class="bg-gray-50 p-6 rounded-lg">
          <div class="text-lg font-medium text-gray-700 mb-3">生成されたコメント:</div>
          <div class="text-xl text-gray-900 leading-relaxed">{{ result.comment }}</div>
        </div>
        
        <div v-if="result.metadata" class="bg-white border rounded-lg p-4">
          <div class="text-sm font-medium text-gray-700 mb-3">天気情報:</div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500">天気条件:</span>
              <span class="ml-2 font-medium">{{ result.metadata.weather_condition }}</span>
            </div>
            <div>
              <span class="text-gray-500">気温:</span>
              <span class="ml-2 font-medium">{{ result.metadata.temperature }}°C</span>
            </div>
            <div>
              <span class="text-gray-500">湿度:</span>
              <span class="ml-2 font-medium">{{ result.metadata.humidity }}%</span>
            </div>
            <div>
              <span class="text-gray-500">風速:</span>
              <span class="ml-2 font-medium">{{ result.metadata.wind_speed }}m/s</span>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t text-xs text-gray-500">
            生成時刻: {{ formatDateTime(result.metadata.generated_at) }}
          </div>
        </div>
      </div>

      <!-- Error Result -->
      <div v-else class="space-y-4">
        <AppAlert
          color="red"
          :title="`${result.location} のコメント生成に失敗しました`"
          :description="result.error"
          icon="heroicons:exclamation-triangle"
        />
      </div>
    </div>

    <!-- Initial State -->
    <div v-else class="text-center py-12">
      <Icon name="heroicons:chat-bubble-left-ellipsis" class="w-16 h-16 text-gray-300 mx-auto mb-4" />
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
  </AppCard>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  generating: boolean
  isBatchMode: boolean
  result: any
  results: any[]
}

const props = defineProps<Props>()

const formatDateTime = (dateString: any) => {
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
</script>
