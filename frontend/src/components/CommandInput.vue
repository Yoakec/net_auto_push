<template>
  <div class="flex flex-col gap-2 p-3 border-t border-gray-800 bg-gray-900 shrink-0">
    <div class="flex items-center gap-2">
      <select
        v-model="selectedSnippet"
        @change="onSnippetSelect"
        class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs flex-1"
      >
        <option value="">Snippets...</option>
        <optgroup v-for="(items, cat) in groupedSnippets" :key="cat" :label="cat">
          <option v-for="s in items" :key="s.command" :value="s.command">{{ s.command }}</option>
        </optgroup>
      </select>
      <button @click="triggerSnippetUpload" class="text-xs text-blue-400 hover:text-blue-300 underline">Upload</button>
    </div>
    <textarea
      v-model="commands"
      placeholder="Enter commands (one per line)..."
      class="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm font-mono resize-none h-20 placeholder-gray-600 focus:outline-none focus:border-blue-500"
      @keydown.enter.ctrl="emit('execute', { commands: parseCommands() })"
    ></textarea>
    <button
      @click="emit('execute', { commands: parseCommands() })"
      class="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
      :disabled="!commands.trim()"
    >
      Execute
    </button>

    <input
      ref="snippetFileInput"
      type="file"
      accept=".csv"
      class="hidden"
      @change="onSnippetFileChange"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  snippets: { type: Array, default: () => [] },
})

const emit = defineEmits(['execute', 'uploadSnippets'])

const commands = ref('')
const selectedSnippet = ref('')
const snippetFileInput = ref(null)

const groupedSnippets = computed(() => {
  const groups = {}
  for (const s of props.snippets) {
    const cat = s.category || 'Uncategorized'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(s)
  }
  return groups
})

function onSnippetSelect() {
  if (selectedSnippet.value) {
    commands.value = selectedSnippet.value
  }
}

function parseCommands() {
  return commands.value.split('\n').map(c => c.trim()).filter(Boolean)
}

function triggerSnippetUpload() {
  snippetFileInput.value?.click()
}

function onSnippetFileChange(e) {
  const file = e.target.files[0]
  if (file) emit('uploadSnippets', file)
}
</script>
