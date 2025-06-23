<template>
  <AppCard>
    <template #header>
      <div class="flex items-center">
        <Icon name="heroicons:clock" class="w-5 h-5 mr-2" />
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
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="font-medium text-sm text-gray-900">{{ item.location }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ formatDate(item.timestamp) }}</div>
          </div>
          <div class="text-xs text-gray-400">{{ item.provider }}</div>
        </div>
        <div v-if="item.comment" class="mt-2 text-sm text-gray-700 line-clamp-2">
          {{ item.comment }}
        </div>
      </div>
    </div>
  </AppCard>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  history: any[]
}

const props = defineProps<Props>()

const formatDate = (timestamp: any) => {
  if (!timestamp) return '不明'
  return new Date(timestamp).toLocaleString('ja-JP', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
