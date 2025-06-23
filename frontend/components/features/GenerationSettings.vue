<template>
  <AppCard>
    <template #header>
      <div class="flex items-center">
        <Icon name="heroicons:cog-6-tooth" class="w-5 h-5 mr-2" />
        <h2 class="text-lg font-semibold">設定</h2>
      </div>
    </template>

    <!-- Batch Mode Toggle -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">生成モード</label>
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
               @click="$emit('update:isBatchMode', !isBatchMode)">
            <span class="pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="isBatchMode ? 'translate-x-6' : 'translate-x-0'">
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Location Selection -->
    <LocationSelector
      :selected-location="selectedLocation"
      :selected-locations="selectedLocations"
      :is-batch-mode="isBatchMode"
      :locations="locations"
      :locations-loading="locationsLoading"
      @update:selected-location="$emit('update:selectedLocation', $event)"
      @update:selected-locations="$emit('update:selectedLocations', $event)"
      @select-all="$emit('selectAll')"
      @clear-all="$emit('clearAll')"
      @select-region="$emit('selectRegion', $event)"
    />

    <!-- LLM Provider Selection -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">LLMプロバイダー</label>
      <select 
        :value="selectedProvider?.value"
        @change="updateProvider($event)"
        class="form-select"
        :disabled="providersLoading"
      >
        <option value="">プロバイダーを選択...</option>
        <option v-for="provider in providerOptions" :key="provider.value" :value="provider.value">
          {{ provider.label }}
        </option>
      </select>
    </div>

    <!-- Weather Forecast Info -->
    <div class="mb-6">
      <AppAlert
        color="blue"
        title="天気予報の仕様"
        icon="heroicons:cloud"
      >
        <template #description>
          <div class="text-sm space-y-1">
            <div>• 予報時刻: 翌日の9:00, 12:00, 15:00, 18:00（JST）</div>
            <div>• 優先順位: 雷・嵐 > 本降りの雨 > 猛暑日熱中症対策 > 雨 > 曇り > 晴れ</div>
          </div>
        </template>
      </AppAlert>
    </div>

    <!-- Current Time -->
    <div class="mb-6">
      <AppAlert
        color="blue"
        :title="`生成時刻: ${currentTime}`"
        icon="heroicons:clock"
      />
    </div>

    <!-- Generate Button -->
    <AppButton
      @click="$emit('generate')"
      :loading="generating"
      :disabled="!canGenerate"
      variant="primary"
      size="lg"
      block
      icon="heroicons:sparkles"
    >
      {{ isBatchMode ? '一括コメント生成' : 'コメント生成' }}
    </AppButton>
  </AppCard>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'

interface Props {
  isBatchMode: boolean
  selectedLocation: string
  selectedLocations: string[]
  selectedProvider: any
  locations: string[]
  locationsLoading: boolean
  providerOptions: any[]
  providersLoading: boolean
  generating: boolean
  currentTime: string
}

interface Emits {
  'update:isBatchMode': [value: boolean]
  'update:selectedLocation': [value: string]
  'update:selectedLocations': [value: string[]]
  'update:selectedProvider': [value: any]
  'generate': []
  'selectAll': []
  'clearAll': []
  'selectRegion': [region: string]
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const canGenerate = computed(() => {
  return (props.isBatchMode && props.selectedLocations.length > 0) || 
         (!props.isBatchMode && props.selectedLocation) && 
         props.selectedProvider && 
         !props.generating
})

const updateProvider = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const provider = props.providerOptions.find(p => p.value === target.value)
  emit('update:selectedProvider', provider)
}
</script>
