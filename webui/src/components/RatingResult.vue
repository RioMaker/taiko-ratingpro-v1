<template>
  <div v-if="data && data.charts && data.charts.length">
    <!-- 谱面选择 -->
    <div v-if="allBranches.length > 1" class="card">
      <h2>🎵 {{ data.title }}</h2>
      <div class="tabs">
        <button
          v-for="(br, i) in allBranches"
          :key="i"
          class="tab-btn"
          :class="{ active: selected === i }"
          @click="selected = i"
        >
          {{ br.course }} {{ br.branch_type !== 'NONE' ? `(${br.branch_type})` : '' }}
        </button>
      </div>
    </div>

    <template v-if="current">
      <!-- 目标难度 -->
      <TargetDifficulty :targets="current.target_difficulties" />

      <!-- 维度评分 -->
      <DimensionChart :dimensions="current.dimensions" />

      <!-- 热点 -->
      <HotspotList
        v-if="current.hotspots && current.hotspots.length"
        :hotspots="current.hotspots"
        :duration="duration"
      />

      <!-- 统计 -->
      <div v-if="current.stats && Object.keys(current.stats).length" class="card">
        <h2>📊 基础统计</h2>
        <div class="stats-grid">
          <div v-for="(val, key) in current.stats" :key="key" class="stat-item">
            <div class="stat-val">{{ formatStat(val) }}</div>
            <div class="stat-label">{{ statLabel(key) }}</div>
          </div>
        </div>
      </div>

      <!-- 摘要 -->
      <div v-if="current.summary" class="card">
        <h2>📝 分析摘要</h2>
        <div class="summary-text">{{ current.summary }}</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TargetDifficulty from './TargetDifficulty.vue'
import DimensionChart from './DimensionChart.vue'
import HotspotList from './HotspotList.vue'

const props = defineProps({ data: Object })
const selected = ref(0)

const allBranches = computed(() => {
  const list = []
  for (const chart of (props.data?.charts || [])) {
    for (const br of (chart.branches || [])) {
      list.push(br)
    }
  }
  return list
})

const current = computed(() => allBranches.value[selected.value] || null)

const duration = computed(() => {
  if (!current.value?.stats) return 0
  return current.value.stats.duration_sec || current.value.stats.duration || 0
})

const STAT_LABELS = {
  total_notes: '总音符数',
  hit_notes: '打击音符',
  duration_sec: '时长(秒)',
  duration: '时长(秒)',
  avg_bpm: '平均BPM',
  max_bpm: '最大BPM',
  min_bpm: '最小BPM',
  nps_mean: '平均NPS',
  nps_max: '最大NPS',
  don_count: '咚数量',
  ka_count: '咔数量',
  big_note_count: '大音符',
  balloon_count: '气球数',
  drumroll_count: '连打数',
}

function statLabel(key) {
  return STAT_LABELS[key] || key
}

function formatStat(val) {
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val : val.toFixed(2)
  }
  return val
}
</script>
