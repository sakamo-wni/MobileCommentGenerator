<template>
  <div class="location-controls">
    <!-- Region Selection -->
    <div class="region-selection">
      <label for="region-select">地方選択:</label>
      <div class="custom-dropdown">
        <select 
          id="region-select"
          :value="selectedRegion"
          @change="$emit('region-change', ($event.target as HTMLSelectElement).value)"
          class="region-select"
        >
          <option value="">すべての地方</option>
          <option v-for="region in regions" :key="region" :value="region">
            {{ region }}
          </option>
        </select>
        <div class="dropdown-arrow">▼</div>
      </div>
    </div>

    <!-- Select All Controls -->
    <div class="select-all-section">
      <div class="select-all-controls">
        <button 
          @click="$emit('select-all')" 
          class="control-btn select-all-btn"
          :disabled="filteredCount === 0"
        >
          すべて選択
        </button>
        <button 
          @click="$emit('clear-all')" 
          class="control-btn clear-all-btn"
          :disabled="selectedCount === 0"
        >
          すべてクリア
        </button>
        <button 
          @click="$emit('select-region')" 
          class="control-btn region-btn"
          :disabled="!selectedRegion || regionLocationCount === 0"
        >
          {{ selectedRegion || '地方' }}を選択
        </button>
      </div>
      <div class="selection-info">
        <span class="selection-count">{{ selectedCount }}地点選択中</span>
        <span class="total-count">/ {{ filteredCount }}地点</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  regions: readonly string[]
  selectedRegion: string
  selectedCount: number
  filteredCount: number
  regionLocationCount: number
}

interface Emits {
  (e: 'region-change', region: string): void
  (e: 'select-all'): void
  (e: 'clear-all'): void
  (e: 'select-region'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<style scoped>
.location-controls {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.region-selection {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.region-selection label {
  font-weight: 600;
  color: #2B2B2B;
  white-space: nowrap;
}

.custom-dropdown {
  position: relative;
  min-width: 200px;
}

.region-select {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 2px solid #E0E8F6;
  border-radius: 8px;
  background: white;
  font-size: 1rem;
  color: #2B2B2B;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease;
}

.region-select:hover {
  border-color: #0C419A;
}

.region-select:focus {
  outline: none;
  border-color: #0C419A;
  box-shadow: 0 0 0 3px rgba(12, 65, 154, 0.1);
}

.dropdown-arrow {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #0C419A;
  font-size: 0.8rem;
}

.select-all-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.select-all-controls {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.control-btn {
  padding: 0.5rem 1rem;
  border: 2px solid #0C419A;
  border-radius: 8px;
  background: white;
  color: #0C419A;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.control-btn:hover:not(:disabled) {
  background: #0C419A;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(12, 65, 154, 0.2);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-all-btn:hover:not(:disabled) {
  background: #0C419A;
}

.clear-all-btn {
  border-color: #dc3545;
  color: #dc3545;
}

.clear-all-btn:hover:not(:disabled) {
  background: #dc3545;
  border-color: #dc3545;
  color: white;
}

.selection-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.selection-count {
  font-weight: 700;
  color: #0C419A;
}

.total-count {
  color: #6C757D;
}

@media (max-width: 768px) {
  .location-controls {
    gap: 1rem;
  }
  
  .region-selection {
    flex-direction: column;
    align-items: stretch;
  }
  
  .select-all-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .select-all-controls {
    justify-content: center;
  }
  
  .selection-info {
    justify-content: center;
  }
}
</style>