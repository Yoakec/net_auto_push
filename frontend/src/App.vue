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
        <TerminalPanel ref="terminalPanel" :task-id="currentTaskId" />
        <ResultCards
          :results="deviceResults"
          :outputs="deviceOutputs"
          @show-modal="openModal"
        />
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
import { ref, onMounted, reactive } from 'vue'
import DeviceTable from './components/DeviceTable.vue'
import TerminalPanel from './components/TerminalPanel.vue'
import CommandInput from './components/CommandInput.vue'
import ResultCards from './components/ResultCards.vue'
import OutputModal from './components/OutputModal.vue'
import ProgressBar from './components/ProgressBar.vue'

const devices = ref([])
const snippets = ref([])
const selectedIps = ref([])
const maxConcurrent = ref(5)
const currentTaskId = ref(null)

const deviceResults = reactive({})
const deviceOutputs = reactive({})

const totalDevices = ref(0)
const completedDevices = ref(0)
const failedDevices = ref(0)

const terminalPanel = ref(null)
const modalDevice = ref(null)
let ws = null

onMounted(async () => {
  await loadInventory()
  await loadSnippets()
})

async function loadInventory() {
  const res = await fetch('/api/inventory')
  devices.value = await res.json()
}

async function loadSnippets() {
  try {
    const res = await fetch('/api/snippets')
    snippets.value = await res.json()
  } catch (e) {
    // no snippets file — ok
  }
}

async function handleUpload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  if (res.ok) {
    await loadInventory()
  }
}

async function handleSnippetUpload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload/snippets', { method: 'POST', body: form })
  if (res.ok) {
    await loadSnippets()
  }
}

async function handleExecute({ commands }) {
  if (!selectedIps.value.length || !commands.length) return

  const res = await fetch('/api/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      device_ips: selectedIps.value,
      commands,
      max_concurrent: maxConcurrent.value,
    }),
  })
  const { task_id } = await res.json()
  currentTaskId.value = task_id

  totalDevices.value = selectedIps.value.length
  completedDevices.value = 0
  failedDevices.value = 0

  Object.keys(deviceResults).forEach(k => delete deviceResults[k])
  Object.keys(deviceOutputs).forEach(k => delete deviceOutputs[k])

  connectWebSocket(task_id)
}

function connectWebSocket(taskId) {
  if (ws) ws.close()
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${location.host}/ws/task/${taskId}`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    switch (msg.type) {
      case 'device_start':
        deviceResults[msg.device_ip] = {
          ip: msg.device_ip,
          type: msg.device_type,
          area: msg.area,
          status: 'running',
          duration_ms: null,
          error: null,
        }
        break
      case 'device_output':
        if (!deviceOutputs[msg.device_ip]) deviceOutputs[msg.device_ip] = {}
        if (!deviceOutputs[msg.device_ip][msg.command]) deviceOutputs[msg.device_ip][msg.command] = ''
        deviceOutputs[msg.device_ip][msg.command] += msg.data
        break
      case 'device_done':
        if (deviceResults[msg.device_ip]) {
          deviceResults[msg.device_ip].status = 'success'
          deviceResults[msg.device_ip].duration_ms = msg.duration_ms
        }
        completedDevices.value++
        break
      case 'device_error':
        if (deviceResults[msg.device_ip]) {
          deviceResults[msg.device_ip].status = 'failed'
          deviceResults[msg.device_ip].error = msg.error
        } else {
          deviceResults[msg.device_ip] = { ip: msg.device_ip, status: 'failed', error: msg.error }
        }
        completedDevices.value++
        failedDevices.value++
        break
      case 'task_progress':
        totalDevices.value = msg.total
        completedDevices.value = msg.completed
        failedDevices.value = msg.failed
        break
      case 'task_complete':
        totalDevices.value = msg.total
        completedDevices.value = msg.total
        failedDevices.value = msg.failed
        break
    }
  }
}

function openModal(device) {
  modalDevice.value = device
}
</script>
