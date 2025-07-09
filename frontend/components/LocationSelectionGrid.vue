<template>
  <div class="location-grid">
    <div 
      v-for="location in locations" 
      :key="location.name"
      class="location-item"
      :class="{ selected: isSelected(location.name) }"
      @click="$emit('toggle', location.name)"
    >
      <div class="location-checkbox">
        <input 
          type="checkbox" 
          :checked="isSelected(location.name)"
          @click.stop
          readonly
        />
      </div>
      <div class="location-details">
        <span class="location-name">{{ location.name }}</span>
        <span class="location-region">{{ location.region || location.area }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Location {
  name: string
  region?: string
  area?: string
}

interface Props {
  locations: Location[]
  selectedLocations: string[]
}

interface Emits {
  (e: 'toggle', location: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isSelected = (locationName: string) => {
  return props.selectedLocations.includes(locationName)
}
</script>

<style scoped>
.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
  max-height: 400px;
  overflow-y: auto;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
}

.location-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border: 2px solid #E0E8F6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.location-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(12, 65, 154, 0.1);
  border-color: #0C419A;
}

.location-item.selected {
  background: linear-gradient(135deg, #E8F0FE 0%, #F0F7FF 100%);
  border-color: #0C419A;
  box-shadow: 0 2px 4px rgba(12, 65, 154, 0.1);
}

.location-checkbox {
  margin-right: 0.75rem;
}

.location-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #0C419A;
}

.location-details {
  display: flex;
  flex-direction: column;
}

.location-name {
  font-weight: 600;
  color: #2B2B2B;
  font-size: 0.95rem;
}

.location-region {
  font-size: 0.8rem;
  color: #6C757D;
  margin-top: 0.15rem;
}

@media (max-width: 768px) {
  .location-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem;
    padding: 0.75rem;
  }
  
  .location-item {
    padding: 0.5rem;
  }
}
</style>