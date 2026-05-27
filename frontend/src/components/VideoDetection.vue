<template>
  <div class="video-detection">
    <div class="video-panel">
      <div class="video-container">
        <div v-if="!hasVideo" class="video-placeholder" @click="triggerFileInput">
          <el-icon class="placeholder-icon"><Monitor /></el-icon>
          <p class="placeholder-text">{{ t('video.uploadHint') }}</p>
          <p class="placeholder-desc">{{ t('video.formats') }}</p>
          <input
            type="file"
            accept="video/*"
            class="video-file-input"
            ref="fileInputRef"
            @change="handleVideoUpload"
          />
        </div>

        <div v-else class="video-content">
          <div class="video-player-wrapper">
            <video
              ref="videoRef"
              :src="videoUrl"
              class="video-player"
              :controls="!isDetecting"
              @loadedmetadata="onVideoLoaded"
              @timeupdate="onTimeUpdate"
              @ended="onVideoEnded"
            />
            <canvas
              ref="canvasRef"
              class="detection-canvas"
              :class="{ 'canvas-active': isDetecting && mode === 'pest' }"
            />
          </div>

          <div v-if="isDetecting" class="realtime-stats">
            <div class="stat-item">
              <span class="stat-label">{{ t('video.currentFrame') }}</span>
              <span class="stat-value">{{ currentFrameIndex }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">{{ t('video.detectedTargets') }}</span>
              <span class="stat-value highlight">{{ currentResult?.total_objects || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">{{ t('video.detectionTime') }}</span>
              <span class="stat-value">{{ currentResult?.detection_time?.toFixed(2) || '0' }}s</span>
            </div>
          </div>

          <div class="video-info">
            <div class="info-row">
              <span class="info-label">{{ t('video.duration') }}</span>
              <span class="info-value">{{ formatDuration(videoDuration) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ t('video.currentTime') }}</span>
              <span class="info-value">{{ formatDuration(currentTime) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="result-panel">
      <div class="result-card">
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span class="card-title">{{ t('video.detectionResult') }}</span>
        </div>

        <div v-if="!hasVideo" class="empty-state">
          <el-icon class="empty-icon"><Upload /></el-icon>
          <p class="empty-text">{{ t('video.uploadFirst') }}</p>
        </div>

        <div v-else-if="!currentResult && !hasResult" class="empty-state">
          <el-icon class="empty-icon"><CircleCheck /></el-icon>
          <p class="empty-text">{{ isDetecting ? t('video.detecting') : t('video.waiting') }}</p>
        </div>

        <div v-else class="result-content">
          <!-- 虫害检测：当前帧检测结果 -->
          <div v-if="mode === 'pest' && currentResult" class="realtime-result">
            <div class="result-summary">
              <div class="summary-item">
                <span class="summary-value">{{ currentResult.total_objects }}</span>
                <span class="summary-label">{{ t('video.currentFrameTargets') }}</span>
              </div>
            </div>

            <div v-if="currentResult.boxes && currentResult.boxes.length > 0" class="detection-list">
              <div v-for="(box, index) in currentResult.boxes" :key="index" class="detection-item">
                <span class="detection-name">{{ box.chinese_name || box.class_name }}</span>
                <span class="detection-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <div v-else class="no-detection">
              <span>{{ t('video.noTargetDetected') }}</span>
            </div>
          </div>

          <!-- 病害检测：当前帧分类结果 -->
          <div v-if="mode === 'disease' && currentResult" class="realtime-result">
            <div class="result-summary">
              <div class="summary-item" v-if="currentResult.top5 && currentResult.top5.length > 0">
                <span class="summary-value">{{ currentResult.top5[0].chinese_name }}</span>
                <span class="summary-label">Top-1 {{ t('video.prediction') }}</span>
              </div>
            </div>

            <div v-if="currentResult.top5 && currentResult.top5.length > 0" class="detection-list">
              <div v-for="(pred, index) in currentResult.top5" :key="index" class="detection-item">
                <span class="detection-name">{{ pred.chinese_name || pred.class_name }}</span>
                <span class="detection-confidence">{{ (pred.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="action-card">
        <div class="action-header">
          <span class="action-title">{{ t('video.settings') }}</span>
        </div>

        <div class="param-section">
          <div v-if="mode === 'pest'" class="param-item">
            <div class="param-label">
              <span>{{ t('video.confidenceThreshold') }}</span>
              <span class="param-value">{{ confidenceThreshold.toFixed(2) }}</span>
            </div>
            <el-slider v-model="confidenceThreshold" :min="0.01" :max="0.9" :step="0.01" :disabled="isDetecting" />
          </div>

          <div class="param-item">
            <div class="param-label">
              <span>{{ t('video.detectionFPS') }}</span>
              <span class="param-value">{{ detectionFPS }} fps</span>
            </div>
            <el-slider v-model="detectionFPS" :min="2" :max="15" :step="1" :disabled="isDetecting" />
          </div>
        </div>

        <div class="action-buttons">
          <el-button size="default" class="btn-upload" @click="triggerFileInput" :disabled="isDetecting">
            <el-icon><Upload /></el-icon>
            {{ t('video.uploadVideo') }}
          </el-button>
          <el-button
            v-if="!isDetecting"
            type="primary"
            size="default"
            class="btn-detect"
            :disabled="!hasVideo"
            @click="startDetection"
          >
            <el-icon><VideoPlay /></el-icon>
            {{ t('video.startDetection') }}
          </el-button>
          <el-button
            v-else
            type="danger"
            size="default"
            class="btn-stop"
            @click="stopDetection"
          >
            <el-icon><VideoPause /></el-icon>
            {{ t('video.stopDetection') }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage } from "element-plus";
import {
  Monitor, Upload, List, CircleCheck, VideoPlay, VideoPause
} from "@element-plus/icons-vue";
import { detectRealtimeFrame, detectDiseaseRealtimeFrame } from "../api/detection";

const props = defineProps({
  mode: { type: String, default: "pest" } // "pest" | "disease"
});

const { t } = useI18n();

const videoRef = ref(null);
const canvasRef = ref(null);
const fileInputRef = ref(null);
const hasVideo = ref(false);
const videoUrl = ref(null);
const videoDuration = ref(0);
const currentTime = ref(0);
const currentFrameIndex = ref(0);

const isDetecting = ref(false);
const currentResult = ref(null);
const hasResult = ref(false);

const confidenceThreshold = ref(0.25);
const detectionFPS = ref(5);

let detectionTimer = null;
let canvasContext = null;
let animationFrameId = null;
let lastBoxes = [];
let lastVideoWidth = 0;
let lastVideoHeight = 0;
let isProcessingFrame = false;

const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return "--:--";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
};

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const handleVideoUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value);

  videoUrl.value = URL.createObjectURL(file);
  hasVideo.value = true;
  currentResult.value = null;
  hasResult.value = false;
  currentFrameIndex.value = 0;
  currentTime.value = 0;

  await nextTick();
  const video = videoRef.value;
  if (video) {
    video.onloadedmetadata = () => { videoDuration.value = video.duration; };
    video.onerror = () => { ElMessage.error(t('video.loadFailed')); hasVideo.value = false; };
  }
};

const onVideoLoaded = () => {
  if (videoRef.value) {
    videoDuration.value = videoRef.value.duration;
    nextTick(() => initCanvas());
  }
};

const onTimeUpdate = () => {
  if (videoRef.value) currentTime.value = videoRef.value.currentTime;
};

const onVideoEnded = () => {
  if (isDetecting.value) {
    stopDetection();
    ElMessage.success(t('video.playComplete'));
  }
};

const initCanvas = () => {
  const video = videoRef.value;
  const canvas = canvasRef.value;
  if (!video || !canvas) return;
  const w = video.clientWidth || video.offsetWidth;
  const h = video.clientHeight || video.offsetHeight;
  canvas.width = w;
  canvas.height = h;
  canvasContext = canvas.getContext("2d");
  canvasContext.clearRect(0, 0, w, h);
};

const clearCanvas = () => {
  if (!canvasContext || !canvasRef.value) return;
  canvasContext.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
};

const drawDetectionBoxes = (boxes, videoWidth, videoHeight, interpolate = false) => {
  if (!canvasContext || !canvasRef.value || !videoRef.value) return;

  const canvas = canvasRef.value;
  const video = videoRef.value;
  const displayWidth = video.clientWidth || video.offsetWidth;
  const displayHeight = video.clientHeight || video.offsetHeight;

  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }

  const scaleX = displayWidth / videoWidth;
  const scaleY = displayHeight / videoHeight;

  canvasContext.clearRect(0, 0, displayWidth, displayHeight);

  let boxesToDraw = boxes;
  if (interpolate && lastBoxes.length > 0 && boxes.length === 0) {
    boxesToDraw = lastBoxes;
    videoWidth = lastVideoWidth;
    videoHeight = lastVideoHeight;
  }

  const colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFE66D", "#FF8E72"];
  boxesToDraw.forEach((box, i) => {
    const x1 = box.x1 * scaleX;
    const y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX;
    const y2 = box.y2 * scaleY;
    const color = colors[i % colors.length];

    canvasContext.strokeStyle = color;
    canvasContext.lineWidth = 2;
    canvasContext.strokeRect(x1, y1, x2 - x1, y2 - y1);

    canvasContext.fillStyle = color;
    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`;
    const labelWidth = canvasContext.measureText(label).width + 10;
    canvasContext.fillRect(x1, y1 - 20, labelWidth, 20);

    canvasContext.fillStyle = "#FFFFFF";
    canvasContext.font = "14px Arial";
    canvasContext.fillText(label, x1 + 5, y1 - 5);
  });

  if (!interpolate) {
    lastBoxes = boxes;
    lastVideoWidth = videoWidth;
    lastVideoHeight = videoHeight;
  }
};

const captureAndDetectFrame = async () => {
  const video = videoRef.value;
  if (!video || video.paused || video.ended || isProcessingFrame) return;

  isProcessingFrame = true;
  try {
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const ctx = tempCanvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise(resolve => {
      tempCanvas.toBlob(b => resolve(b), "image/jpeg", 0.6);
    });

    if (!blob) { isProcessingFrame = false; return; }

    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");
    if (props.mode === "pest") {
      formData.append("confidence_threshold", String(confidenceThreshold.value));
      formData.append("iou_threshold", "0.7");
    }

    const apiFn = props.mode === "disease" ? detectDiseaseRealtimeFrame : detectRealtimeFrame;
    const response = await apiFn(formData);

    if (response.success && response.data) {
      currentResult.value = response.data;
      hasResult.value = true;

      if (props.mode === "pest" && response.data.boxes) {
        drawDetectionBoxes(response.data.boxes, response.data.image_width, response.data.image_height);
      }
      currentFrameIndex.value++;
    }
  } catch (error) {
    console.error("帧检测失败:", error);
  } finally {
    isProcessingFrame = false;
  }
};

const animateCanvas = () => {
  if (!isDetecting.value) return;
  const video = videoRef.value;
  if (video && !video.paused && !video.ended && lastBoxes.length > 0 && lastVideoWidth > 0 && props.mode === "pest") {
    drawDetectionBoxes([], lastVideoWidth, lastVideoHeight, true);
  }
  animationFrameId = requestAnimationFrame(animateCanvas);
};

const startDetection = async () => {
  const video = videoRef.value;
  if (!video) { ElMessage.error(t('video.videoNotLoaded')); return; }

  if (video.readyState < 2) {
    ElMessage.info(t('video.loadingVideo'));
    await new Promise(resolve => {
      video.onloadeddata = resolve;
      video.onerror = () => { ElMessage.error(t('video.loadFailed')); resolve(); };
      setTimeout(resolve, 10000);
    });
  }

  if (video.readyState < 2) { ElMessage.error(t('video.loadFailed')); return; }

  isDetecting.value = true;
  currentResult.value = null;
  currentFrameIndex.value = 0;
  lastBoxes = [];
  isProcessingFrame = false;

  nextTick(() => { initCanvas(); clearCanvas(); });
  await nextTick();

  try {
    await video.play();
  } catch (err) {
    console.error("播放失败:", err);
    ElMessage.warning(t('video.autoplayBlocked'));
  }

  if (props.mode === "pest") animateCanvas();

  const intervalMs = Math.floor(1000 / detectionFPS.value);
  detectionTimer = setInterval(captureAndDetectFrame, intervalMs);
};

const stopDetection = () => {
  if (detectionTimer) { clearInterval(detectionTimer); detectionTimer = null; }
  if (animationFrameId) { cancelAnimationFrame(animationFrameId); animationFrameId = null; }
  if (videoRef.value) videoRef.value.pause();
  isDetecting.value = false;
  clearCanvas();
  lastBoxes = [];
  isProcessingFrame = false;
};

onUnmounted(() => {
  stopDetection();
  if (videoUrl.value) URL.revokeObjectURL(videoUrl.value);
});
</script>

<style scoped lang="scss">
.video-detection {
  display: flex;
  gap: 24px;
  height: 100%;
}

.video-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-container {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: var(--primary-color, #409eff);
    background: rgba(64, 158, 255, 0.05);
  }

  .placeholder-icon { font-size: 64px; color: #909399; margin-bottom: 16px; }
  .placeholder-text { font-size: 16px; color: #606266; margin: 8px 0; }
  .placeholder-desc { font-size: 14px; color: #909399; }
}

.video-file-input { display: none; }

.video-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-player-wrapper {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-player { width: 100%; display: block; }

.detection-canvas {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
  &.canvas-active { opacity: 1; }
}

.realtime-stats {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.stat-item { display: flex; flex-direction: column; }
.stat-label { font-size: 12px; opacity: 0.8; }
.stat-value { font-size: 18px; font-weight: 600; }
.stat-value.highlight { color: #ffd04b; }

.video-info {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.info-row { display: flex; align-items: center; gap: 8px; }
.info-label { color: #909399; font-size: 14px; }
.info-value { color: #303133; font-size: 14px; font-weight: 500; }

.result-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow-y: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.card-title { font-size: 16px; font-weight: 600; color: #303133; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;

  .empty-icon { font-size: 48px; margin-bottom: 16px; }
  .empty-text { font-size: 16px; color: #606266; margin: 8px 0; }
}

.result-content { display: flex; flex-direction: column; gap: 16px; }

.result-summary { display: flex; gap: 16px; }

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-value { font-size: 28px; font-weight: 700; color: var(--primary-color, #409eff); }
.summary-label { font-size: 12px; color: #909399; margin-top: 4px; }

.realtime-result { display: flex; flex-direction: column; gap: 12px; }

.detection-list { display: flex; flex-wrap: wrap; gap: 8px; }

.detection-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.detection-name { color: #303133; }
.detection-confidence { color: var(--primary-color, #409eff); font-weight: 500; }

.no-detection {
  padding: 20px;
  text-align: center;
  color: #909399;
  background: #f5f7fa;
  border-radius: 8px;
}

.action-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.action-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.action-title { font-size: 16px; font-weight: 600; color: #303133; }

.param-section { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }

.param-item { display: flex; flex-direction: column; gap: 8px; }

.param-label { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #606266; }
.param-value { color: var(--primary-color, #409eff); font-weight: 500; }

.action-buttons { display: flex; gap: 12px; }
.btn-upload { flex: 1; }
.btn-detect, .btn-stop { flex: 2; }
</style>
