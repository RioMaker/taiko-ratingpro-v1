<template>
  <header>
    <h1>🥁 太鼓达人谱面难度评定系统</h1>
    <p>上传 TJA 谱面文件，获取多维难度分析</p>
  </header>

  <FileUpload @result="onResult" @error="onError" @loading="onLoading" />

  <div v-if="loading" class="loading">
    <div class="spinner"></div>
    <p style="margin-top: 12px; color: var(--text-muted)">正在分析谱面…</p>
  </div>

  <div v-if="error" class="error-msg">{{ error }}</div>

  <RatingResult v-if="result && !loading" :data="result" />
</template>

<script setup>
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import RatingResult from './components/RatingResult.vue'

const result = ref(null)
const error = ref('')
const loading = ref(false)

function onResult(data) {
  result.value = data
  error.value = ''
}

function onError(msg) {
  error.value = msg
  result.value = null
}

function onLoading(v) {
  loading.value = v
}
</script>
