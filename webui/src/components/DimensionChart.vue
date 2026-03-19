<template>
  <div class="card">
    <h2>📐 基础维度评分</h2>
    <div class="dim-list">
      <div v-for="dim in dimensions" :key="dim.name" class="dim-row">
        <div class="dim-label">{{ dimLabel(dim.name) }}</div>
        <div class="dim-bar-wrap">
          <div
            class="dim-bar"
            :style="{ width: barWidth(dim.normalized), background: barColor(dim.normalized) }"
          ></div>
        </div>
        <div class="dim-value">{{ dim.normalized.toFixed(2) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ dimensions: Array })

const DIM_LABELS = {
  peak_pressure: '瞬间压力',
  sustained_pressure: '持续压力',
  technique_complexity: '技术复杂度',
  rhythm_complexity: '节奏复杂度',
  reading_complexity: '读谱复杂度',
  accuracy_pressure: '精准压力',
  miss_penalty: '容错惩罚',
}

function dimLabel(name) {
  return DIM_LABELS[name] || name
}

function barWidth(normalized) {
  const pct = Math.min(normalized / 10 * 100, 100)
  return `${pct}%`
}

function barColor(normalized) {
  const ratio = normalized / 10
  if (ratio < 0.3) return '#2ecc71'
  if (ratio < 0.6) return '#f39c12'
  if (ratio < 0.8) return '#e67e22'
  return '#e74c3c'
}
</script>
