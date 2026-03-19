<template>
  <div class="card">
    <h2>🔥 难点分布</h2>

    <!-- 时间轴 -->
    <div class="hotspot-timeline" v-if="duration > 0">
      <div class="hotspot-track">
        <div
          v-for="(h, i) in hotspots"
          :key="i"
          class="hotspot-mark"
          :style="markStyle(h)"
          :title="`${h.start.toFixed(1)}s - ${h.end.toFixed(1)}s`"
          @click="selectedIdx = selectedIdx === i ? -1 : i"
        ></div>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
        <span>0s</span>
        <span>{{ duration.toFixed(0) }}s</span>
      </div>
    </div>

    <!-- 选中详情 -->
    <div v-if="selectedIdx >= 0 && hotspots[selectedIdx]" class="hotspot-detail">
      <strong>{{ hotspots[selectedIdx].start.toFixed(1) }}s – {{ hotspots[selectedIdx].end.toFixed(1) }}s</strong>
      （严重度 {{ hotspots[selectedIdx].severity.toFixed(2) }}）
      <br />
      <span v-if="hotspots[selectedIdx].primary_dimensions.length">
        主要维度: {{ hotspots[selectedIdx].primary_dimensions.join(', ') }}
      </span>
      <br v-if="hotspots[selectedIdx].explanation" />
      <span>{{ hotspots[selectedIdx].explanation }}</span>
    </div>

    <!-- 列表 -->
    <table class="hotspot-list-table">
      <thead>
        <tr>
          <th>时间段</th>
          <th>严重度</th>
          <th>主要维度</th>
          <th>影响目标</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(h, i) in hotspots"
          :key="i"
          style="cursor: pointer;"
          @click="selectedIdx = i"
          :style="{ background: selectedIdx === i ? 'rgba(231,76,60,0.1)' : '' }"
        >
          <td>{{ h.start.toFixed(1) }}s – {{ h.end.toFixed(1) }}s</td>
          <td>{{ h.severity.toFixed(2) }}</td>
          <td>{{ h.primary_dimensions.join(', ') }}</td>
          <td>{{ h.affected_targets.join(', ') }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  hotspots: Array,
  duration: Number,
})

const selectedIdx = ref(-1)

function markStyle(h) {
  const dur = props.duration || 1
  const left = (h.start / dur) * 100
  const width = Math.max(((h.end - h.start) / dur) * 100, 0.5)
  const alpha = 0.3 + h.severity * 0.7
  return {
    left: `${left}%`,
    width: `${width}%`,
    background: `rgba(231, 76, 60, ${alpha})`,
  }
}
</script>
