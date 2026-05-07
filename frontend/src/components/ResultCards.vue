<template>
  <div class="flex gap-2 p-3 overflow-x-auto shrink-0" v-if="cards.length">
    <div
      v-for="r in cards"
      :key="r.ip"
      @click="emit('showModal', r)"
      class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors shrink-0"
      :class="r.status === 'success' ? 'bg-emerald-900/50 hover:bg-emerald-900 border border-emerald-700' :
               r.status === 'failed' ? 'bg-red-900/50 hover:bg-red-900 border border-red-700' :
               'bg-gray-800 border border-gray-700'"
    >
      <span class="text-lg">{{ r.status === 'success' ? '✓' : r.status === 'failed' ? '✗' : '⋯' }}</span>
      <div>
        <div class="text-sm font-mono">{{ r.ip }}</div>
        <div class="text-xs text-gray-400">
          <template v-if="r.status === 'success'">{{ r.duration_ms }}ms</template>
          <template v-else-if="r.status === 'failed'">{{ r.error }}</template>
          <template v-else>running</template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  results: { type: Object, default: () => ({}) },
  outputs: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['showModal'])

const cards = computed(() => Object.values(props.results))
</script>
