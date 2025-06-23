<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-4">Pinia Store Test</h1>
    
    <!-- Comment Store Section -->
    <div class="mb-8">
      <h2 class="text-xl font-semibold mb-2">Comment Store</h2>
      <pre class="bg-gray-100 p-2 rounded mb-2">{{ commentStoreState }}</pre>
      <div class="space-x-2">
        <button @click="testCommentGenerating" class="px-4 py-2 bg-blue-500 text-white rounded">
          Toggle Generating
        </button>
        <button @click="testCommentResult" class="px-4 py-2 bg-green-500 text-white rounded">
          Set Test Result
        </button>
        <button @click="commentStore.clearResults()" class="px-4 py-2 bg-red-500 text-white rounded">
          Clear Results
        </button>
      </div>
    </div>
    
    <!-- Location Store Section -->
    <div class="mb-8">
      <h2 class="text-xl font-semibold mb-2">Location Store</h2>
      <pre class="bg-gray-100 p-2 rounded mb-2">{{ locationStoreState }}</pre>
      <div class="space-x-2 mb-2">
        <button @click="locationStore.toggleBatchMode()" class="px-4 py-2 bg-purple-500 text-white rounded">
          Toggle Batch Mode
        </button>
        <button @click="testLocationSelection" class="px-4 py-2 bg-indigo-500 text-white rounded">
          Set Test Location
        </button>
        <button @click="locationStore.clearSelections()" class="px-4 py-2 bg-red-500 text-white rounded">
          Clear Selections
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCommentStore } from '~/stores/comment'
import { useLocationStore } from '~/stores/location'

const commentStore = useCommentStore()
const locationStore = useLocationStore()

// ストアの状態を確認用に展開
const commentStoreState = computed(() => ({
  generating: commentStore.generating,
  result: commentStore.result,
  results: commentStore.results,
  hasResults: commentStore.hasResults,
  successCount: commentStore.successCount
}))

const locationStoreState = computed(() => ({
  selectedLocation: locationStore.selectedLocation,
  selectedLocations: locationStore.selectedLocations,
  isBatchMode: locationStore.isBatchMode,
  canGenerate: locationStore.canGenerate,
  selectedCount: locationStore.selectedCount
}))

// テスト関数
const testCommentGenerating = () => {
  commentStore.setGenerating(!commentStore.generating)
}

const testCommentResult = () => {
  commentStore.setResult({
    success: true,
    location: 'テスト地点',
    comment: 'テストコメント',
    metadata: { test: true }
  })
}

const testLocationSelection = () => {
  if (locationStore.isBatchMode) {
    locationStore.setSelectedLocations(['東京', '大阪', '名古屋'])
  } else {
    locationStore.setSelectedLocation('東京')
  }
}
</script>