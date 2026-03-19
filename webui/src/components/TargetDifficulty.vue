<template>
  <div class="card">
    <h2>🎯 目标难度</h2>
    <div class="target-grid">
      <div class="target-card target-pass">
        <div class="label">通关 Pass</div>
        <div class="value">{{ fmt(targets.pass) }}</div>
      </div>
      <div class="target-card target-fc">
        <div class="label">全连 FC</div>
        <div class="value">{{ fmt(targets.fc) }}</div>
      </div>
      <div class="target-card target-acc">
        <div class="label">全良 ACC</div>
        <div class="value">{{ fmt(targets.acc) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ targets: Object })

function fmt(v) {
  if (v == null) return '-'
  return v.toFixed(2)
}
</script>
