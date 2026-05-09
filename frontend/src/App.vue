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

        <!-- Result cards -->
        <div class="flex gap-2 p-3 overflow-x-auto shrink-0 min-h-[56px] border-t border-gray-800 bg-gray-900/50">
          <template v-if="Object.keys(deviceStates).length">
            <div
              v-for="(info, ip) in deviceStates"
              :key="ip"
              @click="openModal(ip)"
              class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors shrink-0"
              :class="info.status === 'success'
                ? 'bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-600'
                : info.status === 'failed' || info.status === 'error'
                ? 'bg-red-900/60 hover:bg-red-900 border border-red-600'
                : 'bg-gray-700 border border-gray-600'"
            >
              <span class="text-lg">{{ info.status === 'success' ? '✓' : info.status === 'failed' || info.status === 'error' ? '✗' : '⋯' }}</span>
              <div>
                <div class="text-sm font-mono text-gray-100">{{ displayLabel(ip) }}</div>
                <div v-if="info.nickname" class="text-xs text-gray-500 font-mono">{{ ip }}</div>
                <div class="text-xs text-gray-300">
                  <template v-if="info.status === 'success'">{{ info.duration_ms }}ms</template>
                  <template v-else-if="info.status === 'failed' || info.status === 'error'">{{ info.error }}</template>
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

    <!-- Modal -->
    <div
      v-if="isModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      @click.self="closeModal"
    >
      <div class="bg-gray-900 border border-gray-700 rounded-lg w-[80vw] h-[70vh] flex flex-col shadow-2xl">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <div>
            <h3 class="text-lg font-mono text-blue-300">{{ displayLabel(currentModalIp) }}</h3>
            <p v-if="currentModalInfo?.nickname" class="text-xs text-gray-500 font-mono">{{ currentModalIp }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="copyModalLog" class="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 transition-colors">
              Copy All
            </button>
            <button @click="exportModalLog" class="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 transition-colors">
              Export TXT
            </button>
            <button @click="closeModal" class="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
          </div>
        </div>

        <!-- Tab bar for multi-command -->
        <div class="flex gap-1 px-4 py-2 border-b border-gray-800" v-if="modalTabs.length > 1">
          <button
            v-for="cmd in modalTabs"
            :key="cmd"
            @click="activeModalTab = cmd"
            class="px-3 py-1 text-xs rounded-t transition-colors"
            :class="activeModalTab === cmd ? 'bg-gray-800 text-blue-300' : 'text-gray-500 hover:text-gray-300'"
          >{{ cmd }}</button>
        </div>

        <div ref="modalTerminal" class="flex-1 min-h-0"></div>

        <div class="flex gap-2 px-4 py-2 border-t border-gray-800 text-xs text-gray-500">
          <span v-if="currentModalInfo?.duration_ms">Duration: {{ currentModalInfo.duration_ms }}ms</span>
          <span :class="currentModalInfo?.status === 'failed' || currentModalInfo?.status === 'error' ? 'text-red-400' : ''">
            Status: {{ currentModalInfo?.status || 'unknown' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import DeviceTable from './components/DeviceTable.vue'
import CommandInput from './components/CommandInput.vue'
import ProgressBar from './components/ProgressBar.vue'

// ── Core state ──
const devices = ref([])
const snippets = ref([])
const selectedIps = ref([])
const maxConcurrent = ref(5)
const currentTaskId = ref(null)

// ── Device state dictionary (keyed by IP) ──
// Format: { '10.1.1.22': { status, type, area, duration_ms, error, log, outputs: { cmd: data } } }
const deviceStates = reactive({})

// ── Modal state ──
const isModalOpen = ref(false)
const currentModalIp = ref('')
const activeModalTab = ref('')
const modalTerminal = ref(null)

let modalTerm = null

const currentModalInfo = computed(() => deviceStates[currentModalIp.value] || null)

function displayLabel(ip) {
  const info = deviceStates[ip]
  return (info?.nickname) || ip
}
const modalTabs = computed(() => {
  const info = currentModalInfo.value
  return info?.outputs ? Object.keys(info.outputs) : []
})

// ── Terminal state ──
const terminalLogs = ref([])
const terminalContainer = ref(null)

const totalDevices = ref(0)
const completedDevices = ref(0)
const failedDevices = ref(0)

let term = null
let fitAddon = null
let ws = null
let lastLogIdx = 0

// ── Main terminal ──
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

// ── Data loading ──
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

// ── Execute ──
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

  // Reset state
  for (const key of Object.keys(deviceStates)) {
    delete deviceStates[key]
  }
  terminalLogs.value = []
  lastLogIdx = 0

  connectWebSocket(task_id)
}

// ── WebSocket ──
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

    const ip = msg.device_ip

    switch (msg.type) {
      case 'device_start':
        if (!deviceStates[ip]) {
          deviceStates[ip] = {
            status: 'running',
            nickname: msg.device_nickname || '',
            type: msg.device_type || 'unknown',
            area: msg.area || '',
            duration_ms: null,
            error: null,
            log: '',
            outputs: {},
          }
        } else {
          deviceStates[ip].status = 'running'
          if (msg.device_nickname) deviceStates[ip].nickname = msg.device_nickname
        }
        terminalLogs.value.push({ text: `[OK] [${displayLabel(ip)}] connected`, style: 'green' })
        writeLogs()
        break

      case 'device_output':
        if (!deviceStates[ip]) {
          deviceStates[ip] = { status: 'running', type: '?', area: '', duration_ms: null, error: null, log: '', outputs: {} }
        }
        if (!deviceStates[ip].outputs[msg.command]) {
          deviceStates[ip].outputs[msg.command] = ''
        }
        deviceStates[ip].outputs[msg.command] += msg.data
        deviceStates[ip].log += msg.data
        break

      case 'device_done':
        if (deviceStates[ip]) {
          deviceStates[ip].status = 'success'
          deviceStates[ip].duration_ms = msg.duration_ms
          if (msg.device_nickname) deviceStates[ip].nickname = msg.device_nickname
        }
        completedDevices.value++
        terminalLogs.value.push({ text: `[OK] [${displayLabel(ip)}] done, ${msg.duration_ms}ms`, style: 'green' })
        writeLogs()
        break

      case 'device_error':
        if (!deviceStates[ip]) {
          deviceStates[ip] = { status: 'error', nickname: msg.device_nickname || '', type: '?', area: '', duration_ms: null, error: msg.error, log: '', outputs: {} }
        } else {
          deviceStates[ip].status = 'error'
          deviceStates[ip].error = msg.error
          if (msg.device_nickname) deviceStates[ip].nickname = msg.device_nickname
          deviceStates[ip].log += `\n[ERROR]: ${msg.error}\n`
        }
        completedDevices.value++
        failedDevices.value++
        terminalLogs.value.push({ text: `[ERR] [${displayLabel(ip)}] ${msg.error}`, style: 'red' })
        writeLogs()
        break

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

// ── Modal logic ──
function openModal(ip) {
  currentModalIp.value = ip
  const info = deviceStates[ip]
  if (info?.outputs) {
    const tabs = Object.keys(info.outputs)
    activeModalTab.value = tabs.length ? tabs[0] : ''
  }
  isModalOpen.value = true
}

function closeModal() {
  isModalOpen.value = false
  currentModalIp.value = ''
  activeModalTab.value = ''
}

// Modal Xterm.js
watch(isModalOpen, (open) => {
  if (open) {
    // Need to wait for DOM to render the modalTerminal ref
    setTimeout(() => {
      if (modalTerminal.value && !modalTerm) {
        modalTerm = new Terminal({
          theme: {
            background: '#0f172a',
            foreground: '#cbd5e1',
          },
          fontSize: 13,
          fontFamily: '"Cascadia Code", "Fira Code", monospace',
          disableStdin: true,
        })
        modalTerm.open(modalTerminal.value)

        // Fit on resize
        const observer = new ResizeObserver(() => {
          try { modalTerm?.fit() } catch (e) { /* may not have fit addon */ }
        })
        observer.observe(modalTerminal.value)
      }
      writeModalOutput()
    }, 50)
  } else {
    if (modalTerm) {
      modalTerm.dispose()
      modalTerm = null
    }
  }
})

watch(activeModalTab, () => writeModalOutput())

function writeModalOutput() {
  if (!modalTerm) return
  modalTerm.clear()
  const info = currentModalInfo.value
  if (!info?.outputs) return
  const data = info.outputs[activeModalTab.value] || ''
  const lines = data.split('\n')
  for (const line of lines) modalTerm.writeln(line)
}

function copyModalLog() {
  const info = currentModalInfo.value
  if (!info) return
  let text
  if (info.outputs && Object.keys(info.outputs).length) {
    text = Object.entries(info.outputs)
      .map(([cmd, data]) => `========== ${cmd} ==========\n${data}`)
      .join('\n\n')
  } else {
    text = info.log || ''
  }
  navigator.clipboard.writeText(text)
}

function exportModalLog() {
  const info = currentModalInfo.value
  if (!info) return
  let text
  if (info.outputs && Object.keys(info.outputs).length) {
    text = Object.entries(info.outputs)
      .map(([cmd, data]) => `========== ${cmd} ==========\n${data}`)
      .join('\n\n')
  } else {
    text = info.log || ''
  }
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const exportName = displayLabel(currentModalIp.value).replace(/[^a-zA-Z0-9一-鿿_-]/g, '_')
  a.download = `${exportName}_output.txt`
  a.click()
  URL.revokeObjectURL(url)
}

onBeforeUnmount(() => {
  if (modalTerm) modalTerm.dispose()
})
</script>
