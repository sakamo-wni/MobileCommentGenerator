<template>
  <div class="selected-summary" v-if="selectedLocations.length > 0">
    <h4>選択済み地点 ({{ selectedLocations.length }})</h4>
    <div class="selected-tags">
      <span 
        v-for="location in displayedLocations" 
        :key="location"
        class="location-tag"
        @click="$emit('remove', location)"
        role="button"
        tabindex="0"
        :aria-label="`${location}を選択解除`"
        @keydown.enter="$emit('remove', location)"
        @keydown.space.prevent="$emit('remove', location)"
      >
        {{ location }}
        <span class="remove-tag" aria-hidden="true">×</span>
      </span>
      <span v-if="hasMoreLocations" class="more-locations">
        他{{ selectedLocations.length - maxDisplayed }}地点...
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  selectedLocations: string[]
  maxDisplayed?: number
}

interface Emits {
  (e: 'remove', location: string): void
}

const props = withDefaults(defineProps<Props>(), {
  maxDisplayed: 10
})

const emit = defineEmits<Emits>()

const displayedLocations = computed(() => {
  return props.selectedLocations.slice(0, props.maxDisplayed)
})

const hasMoreLocations = computed(() => {
  return props.selectedLocations.length > props.maxDisplayed
})
</script>

<style scoped>
.selected-summary {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  border: 1px solid #E0E8F6;
}

.selected-summary h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2B2B2B;
  margin-bottom: 1rem;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.location-tag {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #E8F0FE 0%, #F0F7FF 100%);
  border: 1px solid #0C419A;
  border-radius: 20px;
  padding: 0.4rem 0.8rem;
  font-size: 0.9rem;
  color: #0C419A;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.location-tag:hover {
  background: #0C419A;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(12, 65, 154, 0.2);
}

.location-tag:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(12, 65, 154, 0.3);
}

.location-tag:active {
  transform: translateY(0);
}

.remove-tag {
  margin-left: 0.4rem;
  font-weight: bold;
  opacity: 0.7;
}

.location-tag:hover .remove-tag {
  opacity: 1;
}

.more-locations {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.8rem;
  font-size: 0.9rem;
  color: #6C757D;
  background: #F8F9FA;
  border-radius: 20px;
  border: 1px solid #DEE2E6;
}

@media (max-width: 768px) {
  .selected-summary {
    padding: 1rem;
    margin-top: 1rem;
  }
  
  .selected-summary h4 {
    font-size: 1rem;
  }
  
  .location-tag {
    font-size: 0.85rem;
    padding: 0.35rem 0.7rem;
  }
}
</style>