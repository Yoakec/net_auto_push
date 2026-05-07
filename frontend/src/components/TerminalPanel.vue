<template>
  <div ref="terminalContainer" class="flex-1 min-h-0 relative"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
  logs: { type: Array, default: () => [] },
})

const terminalContainer = ref(null)
let term = null
let fitAddon = null
let lastIdx = 0

onMounted(() => {
  term = new Terminal({
    theme: {
      background: '#0f172a',
      foreground: '#cbd5e1',
      cursor: '#38bdf8',
      selectionBackground: '#334155',
      black: '#1e293b',
      red: '#ef4444',
      green: '#22c55e',
      yellow: '#eab308',
      blue: '#3b82f6',
      magenta: '#a855f7',
      cyan: '#06b6d4',
      white: '#e2e8f0',
      brightBlack: '#475569',
      brightRed: '#f87171',
      brightGreen: '#4ade80',
      brightYellow: '#facc15',
      brightBlue: '#60a5fa',
      brightMagenta: '#c084fc',
      brightCyan: '#22d3ee',
      brightWhite: '#f8fafc',
    },
    fontSize: 13,
    fontFamily: '"Cascadia Code", "Fira Code", monospace',
    cursorBlink: true,
    allowProposedApi: true,
  })

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalContainer.value)
  fitAddon.fit()

  const observer = new ResizeObserver(() => fitAddon.fit())
  observer.observe(terminalContainer.value)

  term.writeln('\x1b[1;36m══════════════════════════════════\x1b[0m')
  term.writeln('\x1b[1;36m  Net Auto Push — Ready\x1b[0m')
  term.writeln('\x1b[1;36m══════════════════════════════════\x1b[0m')
  term.writeln('')
})

watch(() => props.logs.length, () => {
  while (lastIdx < props.logs.length) {
    const entry = props.logs[lastIdx]
    lastIdx++

    if (typeof entry === 'string') {
      term.writeln(entry)
      continue
    }

    let text = entry.text || ''
    let colorCode = ''
    if (entry.style === 'green') colorCode = '0;32'
    else if (entry.style === 'red') colorCode = '0;31'
    else if (entry.style === 'yellow') colorCode = '0;33'
    else if (entry.style === 'green bold') colorCode = '1;32'

    if (colorCode) {
      term.writeln(`\x1b[${colorCode}m${text}\x1b[0m`)
    } else {
      term.writeln(text)
    }
  }
})

onBeforeUnmount(() => {
  if (term) term.dispose()
})
</script>
