<template>
  <div class="split-pane" :style="{ cursor: dragging ? 'col-resize' : 'default' }">
    <div class="pane left-pane" :style="{ width: leftWidth + 'px' }">
      <slot name="left" />
    </div>
    <div
      class="divider"
      @mousedown="startDrag"
      role="separator"
      aria-orientation="vertical"
      tabindex="0"
      @keydown="onKeydown"
    />
    <div class="pane right-pane">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = withDefaults(
  defineProps<{ defaultLeftWidth?: number; minLeft?: number; minRight?: number }>(),
  { defaultLeftWidth: 420, minLeft: 280, minRight: 280 }
)

const leftWidth = ref(props.defaultLeftWidth)
const dragging = ref(false)
let startX = 0
let startWidth = 0

function startDrag(e: MouseEvent) {
  dragging.value = true
  startX = e.clientX
  startWidth = leftWidth.value
  e.preventDefault()
}

function onMouseMove(e: MouseEvent) {
  if (!dragging.value) return
  const delta = e.clientX - startX
  const container = document.querySelector('.split-pane') as HTMLElement
  const total = container?.offsetWidth ?? window.innerWidth
  const newWidth = Math.min(
    total - props.minRight - 8,
    Math.max(props.minLeft, startWidth + delta)
  )
  leftWidth.value = newWidth
}

function onMouseUp() {
  dragging.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') leftWidth.value = Math.max(props.minLeft, leftWidth.value - 20)
  if (e.key === 'ArrowRight') leftWidth.value = leftWidth.value + 20
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.split-pane {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.pane {
  overflow: auto;
  height: 100%;
}

.left-pane {
  flex-shrink: 0;
}

.right-pane {
  flex: 1;
  min-width: 0;
}

.divider {
  width: 8px;
  flex-shrink: 0;
  background: #f0f0f0;
  cursor: col-resize;
  transition: background 0.2s;
  position: relative;
}

.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 40px;
  background: #d9d9d9;
  border-radius: 1px;
}

.divider:hover,
.divider:focus {
  background: #e6f4ff;
  outline: none;
}
</style>
