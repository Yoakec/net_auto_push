<template>
  <div class="flex flex-col h-screen bg-gray-950 text-gray-100">
    <header class="flex items-center gap-4 px-4 py-3 bg-gray-900 border-b border-gray-800 shrink-0">
      <h1 class="text-lg font-bold text-blue-400 whitespace-nowrap">Net Auto Push</h1>
      <div class="flex items-center gap-3 ml-auto">
        <label class="text-sm text-gray-400">
          Concurrency:
          <select v-model="maxConcurrent" class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm ml-1">
            <option v-for="n in 10" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
        <ProgressBar :total="totalDevices" :completed="completedDevices" :failed="failedDevices" />
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <aside class="w-[30%] min-w-[320px] flex flex-col border-r border-gray-800 bg-gray-900 overflow-hidden">
        <DeviceTable
          :devices="devices"
          :selected="selectedIps"
          @update:selected="selectedIps = $event"
          @upload="handleUpload"
        />
        <CommandInput
          :snippets="snippets"
          @execute="handleExecute"
          @upload-snippets="handleSnippetUpload"
        />
      </aside>

      <main class="flex-1 flex flex-col overflow-hidden">
        <div ref="terminalContainer" class="flex-1 min-h-0 relative"></div>

        <!-- Result cards inline -->
        <div class="flex gap-2 p-3 overflow-x-auto shrink-0 min-h-[56px] border-t border-gray-800 bg-gray-900/50">
          <template v-if="deviceResults.length">
            <div
              v-for="r in deviceResults"
              :key="r.ip"
              @click="openModal(r)"
              class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors shrink-0"
              :class="r.status === 'success' ? 'bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-600' :
                       r.status === 'failed' ? 'bg-red-900/60 hover:bg-red-900 border border-red-600' :
                       'bg-gray-700 border border-gray-600'"
            >
              <span class="text-lg">{{ r.status === 'success' ? '✓' : r.status === 'failed' ? '✗' : '⋯' }}</span>
              <div>
                <div class="text-sm font-mono text-gray-100">{{ r.ip }}</div>
                <div class="text-xs text-gray-300">
                  <template v-if="r.status === 'success'">{{ r.duration_ms }}ms</template>
                  <template v-else-if="r.status === 'failed'">{{ r.error }}</template>
                  <template v-else>running...</template>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="flex items-center text-xs text-gray-600 italic">
            No results yet — select devices and execute a command
          </div>
        </div>
      </main>
    </div>

    <OutputModal
      v-if="modalDevice"
      :device="modalDevice"
      :outputs="deviceOutputs[modalDevice.ip] || {}"
      @close="modalDevice = null"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import DeviceTable from './components/DeviceTable.vue'
import CommandInput from './components/CommandInput.vue'
import OutputModal from './components/OutputModal.vue'
import ProgressBar from './components/ProgressBar.vue'

const devices = ref([])
const snippets = ref([])
const selectedIps = ref([])
const maxConcurrent = ref(5)
const currentTaskId = ref(null)

const deviceResults = ref([])
const deviceOutputs = ref({})
const terminalLogs = ref([])

const totalDevices = ref(0)
const completedDevices = ref(0)
const failedDevices = ref(0)

const terminalContainer = ref(null)
const modalDevice = ref(null)

let term = null
let fitAddon = null
let ws = null
let lastLogIdx = 0

onMounted(async () => {
  initTerminal()
  await loadInventory()
  await loadSnippets()
})

function initTerminal() {
  term = new Terminal({
    theme: {
      background: '#0f172a',
      foreground: '#cbd5e1',
      cursor: '#38bdf8',
      selectionBackground: '#334155',
      black: '#1e293b', red: '#ef4444', green: '#22c55e', yellow: '#eab308',
      blue: '#3b82f6', magenta: '#a855f7', cyan: '#06b6d4', white: '#e2e8f0',
      brightBlack: '#475569', brightRed: '#f87171', brightGreen: '#4ade80',
      brightYellow: '#facc15', brightBlue: '#60a5fa', brightMagenta: '#c084fc',
      brightCyan: '#22d3ee', brightWhite: '#f8fafc',
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
  new ResizeObserver(() => fitAddon.fit()).observe(terminalContainer.value)
  term.writeln('\x1b[1;36m══════════════════════════════════\x1b[0m')
  term.writeln('\x1b[1;36m  Net Auto Push — Ready\x1b[0m')
  term.writeln('\x1b[1;36m══════════════════════════════════\x1b[0m')
  term.writeln('')
}

function writeLogs() {
  while (lastLogIdx < terminalLogs.value.length) {
    const entry = terminalLogs.value[lastLogIdx++]
    if (typeof entry === 'string') { term.writeln(entry); continue }
    const text = entry.text || ''
    let code = ''
    if (entry.style === 'green') code = '0;32'
    else if (entry.style === 'red') code = '0;31'
    else if (entry.style === 'yellow') code = '0;33'
    else if (entry.style === 'green bold') code = '1;32'
    term.writeln(code ? `\x1b[${code}m${text}\x1b[0m` : text)
  }
}

async function loadInventory() {
  const res = await fetch('/api/inventory')
  devices.value = await res.json()
}

async function loadSnippets() {
  try {
    const res = await fetch('/api/snippets')
    snippets.value = await res.json()
  } catch (e) { /* ok */ }
}

async function handleUpload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  if (res.ok) await loadInventory()
}

async function handleSnippetUpload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload/snippets', { method: 'POST', body: form })
  if (res.ok) await loadSnippets()
}

async function handleExecute({ commands }) {
  if (!selectedIps.value.length || !commands.length) return

  const res = await fetch('/api/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      device_ips: [...selectedIps.value],
      commands,
      max_concurrent: maxConcurrent.value,
    }),
  })
  const { task_id } = await res.json()
  currentTaskId.value = task_id

  totalDevices.value = selectedIps.value.length
  completedDevices.value = 0
  failedDevices.value = 0

  deviceResults.value = []
  deviceOutputs.value = {}
  terminalLogs.value = []
  lastLogIdx = 0

  connectWebSocket(task_id)
}

function connectWebSocket(taskId) {
  if (ws) ws.close()
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${location.host}/ws/task/${taskId}`)

  ws.onopen = () => {
    console.log('[WS] connected, task:', taskId)
    terminalLogs.value.push(`[WS] Connected to task ${taskId}`)
    writeLogs()
  }

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    console.log('[WS] msg:', msg.type, msg)

    switch (msg.type) {
      case 'device_start': {
        const item = {
          ip: msg.device_ip,
          type: msg.device_type,
          area: msg.area,
          status: 'running',
          duration_ms: null,
          error: null,
        }
        deviceResults.value.push(item)
        console.log('[WS] deviceResults after push:', deviceResults.value.length)
        terminalLogs.value.push({ text: `[OK] [${msg.device_ip}] connected`, style: 'green' })
        writeLogs()
        break
      }
      case 'device_output':
        if (!deviceOutputs.value[msg.device_ip]) deviceOutputs.value[msg.device_ip] = {}
        if (!deviceOutputs.value[msg.device_ip][msg.command]) deviceOutputs.value[msg.device_ip][msg.command] = ''
        deviceOutputs.value[msg.device_ip][msg.command] += msg.data
        break

      case 'device_done': {
        const r = deviceResults.value.find(d => d.ip === msg.device_ip)
        if (r) {
          r.status = 'success'
          r.duration_ms = msg.duration_ms
        }
        completedDevices.value++
        terminalLogs.value.push({ text: `[OK] [${msg.device_ip}] done, ${msg.duration_ms}ms`, style: 'green' })
        writeLogs()
        break
      }
      case 'device_error': {
        let r = deviceResults.value.find(d => d.ip === msg.device_ip)
        if (r) {
          r.status = 'failed'
          r.error = msg.error
        } else {
          deviceResults.value.push({ ip: msg.device_ip, status: 'failed', error: msg.error, type: '?', area: '', duration_ms: null })
        }
        completedDevices.value++
        failedDevices.value++
        terminalLogs.value.push({ text: `[ERR] [${msg.device_ip}] ${msg.error}`, style: 'red' })
        writeLogs()
        break
      }
      case 'task_progress':
        totalDevices.value = msg.total
        completedDevices.value = msg.completed
        failedDevices.value = msg.failed
        terminalLogs.value.push({ text: `[PROGRESS] ${msg.completed}/${msg.total} done, ${msg.running} running, ${msg.failed} failed`, style: 'yellow' })
        writeLogs()
        break

      case 'task_complete':
        totalDevices.value = msg.total
        completedDevices.value = msg.total
        failedDevices.value = msg.failed
        terminalLogs.value.push({ text: '' })
        terminalLogs.value.push({ text: `══════ Task complete: ${msg.success} success, ${msg.failed} failed ══════`, style: 'green bold' })
        writeLogs()
        break
    }
  }

  ws.onerror = (err) => {
    console.error('[WS] error:', err)
    terminalLogs.value.push({ text: '[WS] Connection error', style: 'red' })
    writeLogs()
  }

  ws.onclose = () => {
    console.log('[WS] disconnected')
    terminalLogs.value.push({ text: '[WS] Disconnected', style: 'yellow' })
    writeLogs()
  }
}

function openModal(device) {
  modalDevice.value = device
}
</script>
