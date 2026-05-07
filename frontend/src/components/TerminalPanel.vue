<template>
  <div ref="terminalContainer" class="flex-1 min-h-0 relative"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({ taskId: String })

const terminalContainer = ref(null)
let term = null
let fitAddon = null
let ws = null

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

  if (props.taskId) connect(props.taskId)
})

watch(() => props.taskId, (id) => {
  if (id) connect(id)
})

function connect(taskId) {
  if (ws) { ws.close(); ws = null }
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${location.host}/ws/task/${taskId}`)

  ws.onopen = () => {
    term.writeln(`\x1b[0;36m[WS]\x1b[0m Connected to task ${taskId}\n`)
  }

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    switch (msg.type) {
      case 'device_start':
        term.writeln(`\x1b[0;32m[OK]\x1b[0m [${msg.device_ip}] connected`)
        break
      case 'device_done':
        term.writeln(`\x1b[0;32m[OK]\x1b[0m [${msg.device_ip}] done, ${msg.duration_ms}ms`)
        break
      case 'device_error':
        term.writeln(`\x1b[0;31m[ERR]\x1b[0m [${msg.device_ip}] ${msg.error}`)
        break
      case 'task_progress':
        term.writeln(`\x1b[0;33m[PROGRESS]\x1b[0m ${msg.completed}/${msg.total} done, ${msg.running} running, ${msg.failed} failed`)
        break
      case 'task_complete':
        term.writeln(`\n\x1b[1;32m══════ Task complete: ${msg.success} success, ${msg.failed} failed ══════\x1b[0m`)
        break
    }
  }

  ws.onclose = () => { term.writeln('\x1b[0;33m[WS]\x1b[0m Disconnected') }
}

onBeforeUnmount(() => {
  if (ws) ws.close()
  if (term) term.dispose()
})
</script>
