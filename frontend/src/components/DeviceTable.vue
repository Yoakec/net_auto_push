<template>
  <div class="flex flex-col overflow-hidden flex-1 p-3">
    <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Devices</h2>

    <div class="flex gap-2 mb-2">
      <select v-model="filterArea" class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs flex-1">
        <option value="">All Areas</option>
        <option v-for="a in areas" :key="a" :value="a">{{ a }}</option>
      </select>
      <select v-model="filterType" class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs flex-1">
        <option value="">All Types</option>
        <option v-for="t in types" :key="t" :value="t">{{ t }}</option>
      </select>
      <input
        v-model="searchText"
        type="text"
        placeholder="Search IP..."
        class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs flex-1 placeholder-gray-600"
      />
    </div>

    <div class="flex items-center gap-2 mb-2 text-xs">
      <label class="flex items-center gap-1 cursor-pointer text-gray-400">
        <input type="checkbox" :checked="allSelected" @change="toggleAll" class="rounded" />
        Select all ({{ filteredDevices.length }})
      </label>
      <button @click="$emit('upload', null)" class="ml-auto text-blue-400 hover:text-blue-300 underline text-xs">
        Upload CSV
      </button>
    </div>

    <div class="flex-1 overflow-auto">
      <table class="w-full text-xs">
        <thead class="sticky top-0 bg-gray-900">
          <tr class="text-gray-500 text-left">
            <th class="w-8 p-1"></th>
            <th class="p-1">IP</th>
            <th class="p-1">Type</th>
            <th class="p-1">Area</th>
            <th class="p-1">Proto</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="d in filteredDevices"
            :key="d.ip"
            class="border-t border-gray-800 hover:bg-gray-800 cursor-pointer"
            @click="toggleDevice(d.ip)"
          >
            <td class="p-1">
              <input type="checkbox" :checked="selected.includes(d.ip)" class="rounded" />
            </td>
            <td class="p-1 font-mono text-blue-300">{{ d.ip }}</td>
            <td class="p-1 text-gray-300">{{ d.type }}</td>
            <td class="p-1 text-gray-400">{{ d.area }}</td>
            <td class="p-1 text-gray-400">{{ d.protocol }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept=".csv"
      class="hidden"
      @change="onFileChange"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  devices: { type: Array, default: () => [] },
  selected: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:selected', 'upload'])

const filterArea = ref('')
const filterType = ref('')
const searchText = ref('')
const fileInput = ref(null)

const areas = computed(() => [...new Set(props.devices.map(d => d.area).filter(Boolean))])
const types = computed(() => [...new Set(props.devices.map(d => d.type).filter(Boolean))])

const filteredDevices = computed(() => {
  return props.devices.filter(d => {
    if (filterArea.value && d.area !== filterArea.value) return false
    if (filterType.value && d.type !== filterType.value) return false
    if (searchText.value && !d.ip.includes(searchText.value)) return false
    return true
  })
})

const allSelected = computed(() =>
  filteredDevices.value.length > 0 && filteredDevices.value.every(d => props.selected.includes(d.ip))
)

function toggleDevice(ip) {
  const s = new Set(props.selected)
  if (s.has(ip)) s.delete(ip); else s.add(ip)
  emit('update:selected', [...s])
}

function toggleAll() {
  if (allSelected.value) {
    const toRemove = new Set(filteredDevices.value.map(d => d.ip))
    emit('update:selected', props.selected.filter(ip => !toRemove.has(ip)))
  } else {
    const s = new Set(props.selected)
    filteredDevices.value.forEach(d => s.add(d.ip))
    emit('update:selected', [...s])
  }
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) emit('upload', file)
}

defineExpose({ fileInput })
</script>
