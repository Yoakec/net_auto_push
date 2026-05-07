<template>
  <div class="flex items-center gap-2 text-xs">
    <div class="h-1.5 flex-1 bg-gray-800 rounded-full overflow-hidden max-w-[120px]">
      <div
        class="h-full bg-blue-500 rounded-full transition-all duration-300"
        :style="{ width: pct + '%' }"
      ></div>
    </div>
    <span class="text-gray-400 tabular-nums whitespace-nowrap">
      {{ completed }}/{{ total }}
      <span v-if="failed" class="text-red-400 ml-1">({{ failed }} err)</span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  completed: { type: Number, default: 0 },
  failed: { type: Number, default: 0 },
})

const pct = computed(() => props.total > 0 ? (props.completed / props.total) * 100 : 0)
</script>
