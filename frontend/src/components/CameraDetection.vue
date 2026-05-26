<template>
  <div class="camera-detection">
    <!-- 控制栏 -->
    <div class="control-bar">
      <div class="control-left">
        <el-button type="primary" @click="startCamera" :disabled="isRunning" :loading="isStarting">
          <el-icon><VideoPlay /></el-icon>{{ t('camera.start') }}
        </el-button>
        <el-button @click="pauseResume" :disabled="!isRunning">
          <el-icon><component :is="isPaused ? 'VideoPlay' : 'VideoPause'" /></el-icon>
          {{ isPaused ? t('camera.resume') : t('camera.pause') }}
        </el-button>
        <el-button type="danger" @click="stopCamera" :disabled="!isRunning">
          <el-icon><VideoCamera /></el-icon>{{ t('camera.stop') }}
        </el-button>
      </div>
      <div class="control-right">
        <span class="stat-item">
          <span class="stat-label">{{ t('camera.status') }}:</span>
          <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
        </span>
        <span class="stat-item">
          <span class="stat-label">{{ t('camera.fps') }}:</span>
          <span class="stat-value">{{ fps }}</span>
        </span>
        <span class="stat-item">
          <span class="stat-label">{{ t('camera.detectionTime') }}:</span>
          <span class="stat-value">{{ detectionTime }}s</span>
        </span>
        <span class="stat-item">
          <span class="stat-label">{{ t('camera.totalObjects') }}:</span>
          <span class="stat-value">{{ totalObjects }}</span>
        </span>
      </div>
    </div>

    <!-- 视频预览区 -->
    <div class="video-container" ref="videoContainer">
      <video
        ref="videoRef"
        class="video-preview"
        autoplay
        playsinline
        muted
        @loadedmetadata="onVideoReady"
      ></video>
      <canvas
        ref="overlayCanvas"
        class="overlay-canvas"
      ></canvas>
      <canvas
        ref="captureCanvas"
        class="capture-canvas"
        style="display:none"
      ></canvas>

      <!-- 未启动时的占位 -->
      <div v-if="!isRunning && !hasEverStarted" class="placeholder">
        <el-icon :size="64" color="#a0aec0"><VideoCamera /></el-icon>
        <p>{{ t('camera.clickToStart') }}</p>
      </div>

      <!-- 暂停覆盖层 -->
      <div v-if="isPaused" class="pause-overlay">
        <el-icon :size="48" color="#fff"><VideoPause /></el-icon>
        <p>{{ t('camera.paused') }}</p>
      </div>
    </div>

    <!-- 检测结果列表 -->
    <div class="detection-list" v-if="detectedTargets.length > 0">
      <div class="list-header">{{ t('camera.detectedTargets') }}</div>
      <div class="list-body">
        <div
          v-for="(target, idx) in detectedTargets"
          :key="idx"
          class="target-item"
          :style="{ borderLeftColor: getBoxColor(target.class_name) }"
        >
          <div class="target-name">
            <span class="color-dot" :style="{ background: getBoxColor(target.class_name) }"></span>
            {{ target.chinese_name }}
          </div>
          <div class="target-conf">{{ (target.confidence * 100).toFixed(1) }}%</div>
        </div>
      </div>
    </div>

    <!-- 摄像头权限引导弹窗 -->
    <el-dialog
      v-model="showPermissionGuide"
      :title="t('camera.permissionGuideTitle')"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="permission-guide">
        <div class="guide-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <div class="step-title">{{ t('camera.findPermissionIcon') }}</div>
            <div class="step-desc">{{ t('camera.permissionIconDesc') }}</div>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <div class="step-title">{{ t('camera.allowCamera') }}</div>
            <div class="step-desc">{{ t('camera.allowCameraDesc') }}</div>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <div class="step-title">{{ t('camera.refreshPage') }}</div>
            <div class="step-desc">{{ t('camera.refreshDesc') }}</div>
          </div>
        </div>
        <div class="browser-tips">
          <div class="tip-title">{{ t('camera.browserSpecific') }}:</div>
          <div class="tip-item">
            <strong>Chrome / Edge:</strong> {{ t('camera.chromeTip') }}
          </div>
          <div class="tip-item">
            <strong>Firefox:</strong> {{ t('camera.firefoxTip') }}
          </div>
          <div class="tip-item">
            <strong>Safari:</strong> {{ t('camera.safariTip') }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="refreshPage">{{ t('camera.refreshAndRetry') }}</el-button>
        <el-button @click="showPermissionGuide = false">{{ t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { VideoCamera, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { detectFrame, startDetection, stopDetection, pauseDetection, resumeDetection } from '../api/detection'

const { t } = useI18n()

// DOM 引用
const videoRef = ref(null)
const overlayCanvas = ref(null)
const captureCanvas = ref(null)
const videoContainer = ref(null)

// 状态
const isRunning = ref(false)
const isPaused = ref(false)
const isStarting = ref(false)
const hasEverStarted = ref(false)
const showPermissionGuide = ref(false)

// 统计数据
const fps = ref(0)
const detectionTime = ref(0)
const totalObjects = ref(0)
const detectedTargets = ref([])

// 内部变量
let videoStream = null
let detectionFrameId = null
let drawFrameId = null
let lastDetectionTime = 0
let currentBoxes = []
let consecutiveErrorCount = 0
const MAX_CONSECUTIVE_ERRORS = 10

// 状态文本
const statusText = computed(() => {
  if (isPaused.value) return t('camera.statusPaused')
  if (isRunning.value) return t('camera.statusRunning')
  return t('camera.statusStopped')
})

const statusType = computed(() => {
  if (isPaused.value) return 'warning'
  if (isRunning.value) return 'success'
  return 'info'
})

// 颜色映射
const colorPalette = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4',
  '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e',
  '#84cc16', '#64748b', '#d946ef', '#0ea5e9', '#78716c'
]

const getBoxColor = (className) => {
  let hash = 0
  for (let i = 0; i < (className || '').length; i++) {
    hash = className.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colorPalette[Math.abs(hash) % colorPalette.length]
}

// 初始化画布
const initCanvas = () => {
  const video = videoRef.value
  const overlay = overlayCanvas.value
  const capture = captureCanvas.value
  if (!video || !overlay || !capture) return

  const w = video.videoWidth || 640
  const h = video.videoHeight || 480
  overlay.width = w
  overlay.height = h
  capture.width = w
  capture.height = h

  if (videoContainer.value) {
    const containerW = videoContainer.value.clientWidth
    const ratio = containerW / w
    overlay.style.width = containerW + 'px'
    overlay.style.height = (h * ratio) + 'px'
  }
}

// 视频就绪
const onVideoReady = () => {
  initCanvas()
}

// 启动摄像头
const startCamera = async () => {
  if (isRunning.value) return

  isStarting.value = true
  try {
    // 启动后端检测服务
    const res = await startDetection({
      confidence_threshold: 0.5,
      iou_threshold: 0.7,
      inference_interval: 2
    })

    if (!res.success) {
      ElMessage.error(res.message || t('camera.startFailed'))
      isStarting.value = false
      return
    }

    // 获取摄像头权限
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 }
      },
      audio: false
    })

    if (videoRef.value) {
      videoRef.value.srcObject = videoStream
      await videoRef.value.play()

      // 等视频就绪后初始化
      await nextTick()
      setTimeout(() => {
        initCanvas()
        isRunning.value = true
        isPaused.value = false
        hasEverStarted.value = true
        consecutiveErrorCount = 0
        currentBoxes = []
        lastDetectionTime = 0

        // 启动循环
        startDrawingLoop()
        startDetectionStream()
      }, 200)
    }

    ElMessage.success(t('camera.started'))
  } catch (error) {
    handleCameraError(error)
  } finally {
    isStarting.value = false
  }
}

// 摄像头错误处理
const handleCameraError = (error) => {
  console.error('摄像头错误:', error)
  switch (error.name) {
    case 'NotAllowedError':
      ElMessage.error(t('camera.notAllowed'))
      showPermissionGuide.value = true
      break
    case 'NotFoundError':
      ElMessage.error(t('camera.notFound'))
      break
    case 'NotReadableError':
      ElMessage.error(t('camera.notReadable'))
      break
    default:
      ElMessage.error(t('camera.cannotAccess'))
  }
  cleanupResources()
  resetState()
}

// 检测流：定时发送帧到后端
const startDetectionStream = () => {
  const sendFrameForDetection = async () => {
    if (!isRunning.value) return

    const currentTime = performance.now()
    const timeSinceLast = currentTime - lastDetectionTime
    const targetInterval = 200 // 每 200ms 发送一次（约 5fps 检测频率）

    if (!videoRef.value || !captureCanvas.value) {
      detectionFrameId = requestAnimationFrame(sendFrameForDetection)
      return
    }

    if (!isPaused.value && timeSinceLast >= targetInterval) {
      try {
        const capture = captureCanvas.value
        const ctx = capture.getContext('2d')
        ctx.drawImage(videoRef.value, 0, 0, capture.width, capture.height)

        const imageData = capture.toDataURL('image/jpeg', 0.7)

        const response = await detectFrame({ image: imageData })

        if (response.success) {
          currentBoxes = response.data.boxes || []
          fps.value = response.data.fps || 0
          detectionTime.value = response.data.detection_time || 0
          totalObjects.value = response.data.total_objects || 0
          consecutiveErrorCount = 0
          lastDetectionTime = currentTime

          // 更新检测目标列表（去重 + 最新）
          updateDetectedTargets(currentBoxes)
        } else {
          consecutiveErrorCount++
          if (consecutiveErrorCount > MAX_CONSECUTIVE_ERRORS) {
            ElMessage.error(t('camera.tooManyErrors'))
            stopCamera()
            return
          }
        }
      } catch (error) {
        consecutiveErrorCount++
        if (consecutiveErrorCount > MAX_CONSECUTIVE_ERRORS) {
          ElMessage.error(t('camera.tooManyErrors'))
          stopCamera()
          return
        }
      }
    }

    detectionFrameId = requestAnimationFrame(sendFrameForDetection)
  }

  sendFrameForDetection()
}

// 绘制检测框循环
const startDrawingLoop = () => {
  const drawBoxes = () => {
    if (!isRunning.value) return

    const canvas = overlayCanvas.value
    const video = videoRef.value
    if (!canvas || !video) {
      drawFrameId = requestAnimationFrame(drawBoxes)
      return
    }

    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (video.videoWidth && video.videoHeight) {
      const scaleX = canvas.width / video.videoWidth
      const scaleY = canvas.height / video.videoHeight

      currentBoxes.forEach((box) => {
        const x1 = box.x1 * scaleX
        const y1 = box.y1 * scaleY
        const x2 = box.x2 * scaleX
        const y2 = box.y2 * scaleY
        const w = x2 - x1
        const h = y2 - y1

        const color = getBoxColor(box.class_name)

        // 绘制边框
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.strokeRect(x1, y1, w, h)

        // 半透明填充
        ctx.fillStyle = color
        ctx.globalAlpha = 0.1
        ctx.fillRect(x1, y1, w, h)
        ctx.globalAlpha = 1

        // 标签
        const label = `${box.chinese_name} ${(box.confidence * 100).toFixed(0)}%`
        ctx.font = 'bold 12px Arial'
        const textMetrics = ctx.measureText(label)
        const labelWidth = textMetrics.width + 8
        const labelHeight = 18

        if (y1 >= labelHeight) {
          ctx.fillStyle = color
          ctx.fillRect(x1, y1 - labelHeight, labelWidth, labelHeight)
          ctx.fillStyle = '#ffffff'
          ctx.fillText(label, x1 + 4, y1 - 5)
        } else {
          ctx.fillStyle = color
          ctx.fillRect(x1, y1 + h, labelWidth, labelHeight)
          ctx.fillStyle = '#ffffff'
          ctx.fillText(label, x1 + 4, y1 + h + 13)
        }
      })
    }

    drawFrameId = requestAnimationFrame(drawBoxes)
  }

  drawBoxes()
}

// 更新已检测目标列表
const updateDetectedTargets = (boxes) => {
  const existing = [...detectedTargets.value]
  boxes.forEach((box) => {
    const idx = existing.findIndex(
      (t) => t.class_name === box.class_name
    )
    if (idx !== -1) {
      existing[idx] = { ...existing[idx], ...box }
    } else {
      existing.push({ ...box })
    }
    // 限制最大显示 20 个
  })
  if (existing.length > 20) {
    existing.splice(0, existing.length - 20)
  }
  detectedTargets.value = existing
}

// 暂停/恢复
const pauseResume = async () => {
  if (isPaused.value) {
    await resumeDetection()
    isPaused.value = false
    ElMessage.success(t('camera.resumed'))
  } else {
    await pauseDetection()
    isPaused.value = true
    ElMessage.info(t('camera.paused'))
  }
}

// 停止摄像头
const stopCamera = async () => {
  isRunning.value = false
  isPaused.value = false

  // 停止所有循环
  if (detectionFrameId) {
    cancelAnimationFrame(detectionFrameId)
    detectionFrameId = null
  }
  if (drawFrameId) {
    cancelAnimationFrame(drawFrameId)
    drawFrameId = null
  }

  // 停止后端检测服务
  await stopDetection()

  cleanupResources()
  resetState()
  ElMessage.info(t('camera.stopped'))
}

// 清理资源
const cleanupResources = () => {
  if (videoStream) {
    videoStream.getTracks().forEach((track) => track.stop())
    videoStream = null
  }
}

// 重置状态
const resetState = () => {
  fps.value = 0
  detectionTime.value = 0
  totalObjects.value = 0
  currentBoxes = []
  detectedTargets.value = []

  if (overlayCanvas.value) {
    const ctx = overlayCanvas.value.getContext('2d')
    ctx.clearRect(0, 0, overlayCanvas.value.width, overlayCanvas.value.height)
  }
}

// 刷新页面
const refreshPage = () =&gt; {
  window.location.reload()
}

// 组件卸载时清理
onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
.camera-detection {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  flex-wrap: wrap;
  gap: 8px;
}

.control-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-right {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.stat-label {
  color: var(--text-secondary, #64748b);
}

.stat-value {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  font-variant-numeric: tabular-nums;
}

.video-container {
  flex: 1;
  position: relative;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  min-height: 300px;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.capture-canvas {
  display: none;
}

.placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.placeholder p {
  font-size: 15px;
  color: #94a3b8;
}

.pause-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 10;
}

.pause-overlay p {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.detection-list {
  background: var(--bg-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  padding: 12px 16px;
  max-height: 200px;
  overflow-y: auto;
}

.list-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 8px;
}

.list-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.target-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: #fff;
  border: 1px solid var(--border-color, #e2e8f0);
  border-left: 3px solid;
  border-radius: 4px;
  font-size: 13px;
}

.target-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.target-conf {
  color: var(--text-secondary, #64748b);
  font-size: 12px;
  margin-left: 4px;
}

.permission-guide {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.guide-step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.step-number {
  width: 36px;
  height: 36px;
  background: var(--el-color-primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 4px;
}

.step-desc {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
  line-height: 1.5;
}

.browser-tips {
  background: var(--el-bg-color-page);
  padding: 16px;
  border-radius: 8px;
  margin-top: 8px;
}

.tip-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 12px;
}

.tip-item {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
  margin-bottom: 8px;
  line-height: 1.5;
}

.tip-item:last-child {
  margin-bottom: 0;
}
</style>
