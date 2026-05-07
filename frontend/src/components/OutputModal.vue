<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70" @click.self="emit('close')">
    <div class="bg-gray-900 border border-gray-700 rounded-lg w-[80vw] h-[70vh] flex flex-col shadow-2xl">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <h3 class="text-lg font-mono text-blue-300">{{ device.ip }}</h3>
        <div class="flex items-center gap-2">
          <button @click="copyAll" class="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 transition-colors">
            Copy All
          </button>
          <button @click="exportTxt" class="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 transition-colors">
            Export TXT
          </button>
          <button @click="emit('close')" class="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
        </div>
      </div>

      <div class="flex gap-1 px-4 py-2 border-b border-gray-800" v-if="commandTabs.length > 1">
        <button
          v-for="cmd in commandTabs"
          :key="cmd"
          @click="activeTab = cmd"
          class="px-3 py-1 text-xs rounded-t transition-colors"
          :class="activeTab === cmd ? 'bg-gray-800 text-blue-300' : 'text-gray-500 hover:text-gray-300'"
        >{{ cmd }}</button>
      </div>

      <div ref="modalTerminal" class="flex-1 min-h-0"></div>

      <div class="flex gap-2 px-4 py-2 border-t border-gray-800 text-xs text-gray-500">
        <span v-if="device.duration_ms">Duration: {{ device.duration_ms }}ms</span>
        <span :class="device.status === 'failed' ? 'text-red-400' : ''">
          Status: {{ device.status }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
  device: Object,
  outputs: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close'])
const modalTerminal = ref(null)
const activeTab = ref('')

let term = null

const commandTabs = computed(() => Object.keys(props.outputs))

onMounted(() => {
  if (commandTabs.value.length) activeTab.value = commandTabs.value[0]
  initTerminal()
  writeOutput()

  const observer = new ResizeObserver(() => {
    if (term) {
      try { term.fit() } catch(e) { /* terminal might not have addon */ }
    }
  })
  observer.observe(modalTerminal.value)
})

watch(activeTab, () => writeOutput())

function initTerminal() {
  if (term) term.dispose()
  term = new Terminal({
    theme: {
      background: '#0f172a',
      foreground: '#cbd5e1',
    },
    fontSize: 13,
    fontFamily: '"Cascadia Code", "Fira Code", monospace',
    disableStdin: true,
  })
  term.open(modalTerminal.value)
}

function writeOutput() {
  if (!term) return
  term.clear()
  const lines = (props.outputs[activeTab.value] || '').split('\n')
  for (const line of lines) term.writeln(line)
}

function copyAll() {
  const parts = Object.entries(props.outputs).map(([cmd, data]) => `========== ${cmd} ==========\n${data}`)
  navigator.clipboard.writeText(parts.join('\n\n'))
}

function exportTxt() {
  const parts = Object.entries(props.outputs).map(([cmd, data]) => `========== ${cmd} ==========\n${data}`)
  const blob = new Blob([parts.join('\n\n')], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.device.ip}_${props.device.type || 'device'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

onBeforeUnmount(() => {
  if (term) term.dispose()
})
</script>
