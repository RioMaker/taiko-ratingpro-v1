<template>
  <div class="card">
    <h2>📄 上传谱面</h2>

    <div
      class="upload-zone"
      :class="{ 'drag-over': dragOver }"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="onDrop"
    >
      <input type="file" accept=".tja" @change="onFileChange" />
      <div class="icon">📁</div>
      <p>拖拽 TJA 文件到此处，或点击选择文件</p>
    </div>

    <details class="paste-area">
      <summary>或直接粘贴 TJA 文本</summary>
      <textarea v-model="pasteText" placeholder="粘贴 TJA 谱面内容…"></textarea>
      <button class="btn btn-primary" :disabled="!pasteText.trim()" @click="submitText">
        分析文本
      </button>
    </details>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['result', 'error', 'loading'])

const dragOver = ref(false)
const pasteText = ref('')

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) uploadFile(file)
}

function onDrop(e) {
  dragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) uploadFile(file)
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith('.tja')) {
    emit('error', '请上传 .tja 格式的谱面文件')
    return
  }
  emit('loading', true)
  emit('error', '')

  const form = new FormData()
  form.append('file', file)

  try {
    const res = await fetch('/api/rate', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok) {
      emit('error', data.error || '请求失败')
    } else {
      emit('result', data)
    }
  } catch (err) {
    emit('error', `网络错误: ${err.message}`)
  } finally {
    emit('loading', false)
  }
}

async function submitText() {
  emit('loading', true)
  emit('error', '')

  try {
    const res = await fetch('/api/rate/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: pasteText.value }),
    })
    const data = await res.json()
    if (!res.ok) {
      emit('error', data.error || '请求失败')
    } else {
      emit('result', data)
    }
  } catch (err) {
    emit('error', `网络错误: ${err.message}`)
  } finally {
    emit('loading', false)
  }
}
</script>
