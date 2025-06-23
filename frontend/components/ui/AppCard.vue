<template>
  <div class="card">
    <div v-if="$slots.header" class="card-header">
      <slot name="header" />
    </div>
    <div class="p-6">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
