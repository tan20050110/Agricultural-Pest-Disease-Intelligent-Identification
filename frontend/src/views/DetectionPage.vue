<template>
  <div class="detection-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span>{{ t('detection.workspace') }}</span>
        <span class="separator">›</span>
        <span class="active">{{ t('detection.title') }}</span>
      </div>
      <h1 class="page-title">{{ t('detection.pageTitle') }}</h1>
      <p class="page-subtitle">
        {{ t('detection.pageSubtitle') }}
      </p>
    </div>


    <!-- 功能选项卡 -->
    <div class="function-tabs">
      <div
        v-for="(tab, index) in functionTabs"
        :key="tab.key"
        class="function-tab"
        :class="{ active: activeTab === tab.key }"
        @click="handleTabClick(tab.key, index)"
      >
        <input
          v-if="tab.key !== 'camera' && tab.key !== 'video'"
          type="file"
          :accept="tab.accept"
          :multiple="tab.multiple"
          class="file-input"
          :ref="el => fileInputs[index] = el"
          @change.stop="handleFileChange($event, tab.key)"
        />
        <el-icon :size="18" class="tab-icon"><component :is="tab.icon" /></el-icon>
        <div class="tab-content">
          <span class="tab-text">{{ t(`detection.${tab.key}`) }}</span>
          <span class="tab-desc">{{ t(`detection.${tab.key}Desc`) }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧检测结果区域 -->
      <div class="left-panel">
        <div class="panel-header">
          <span class="panel-title">{{ t('detection.detectionPreview') }}</span>
          <el-tag
            :type="hasImage && detectionResult ? 'success' : 'info'"
            effect="light"
            class="result-tag"
          >
            <el-icon class="el-icon--left" v-if="hasImage && detectionResult"><Check /></el-icon>
            <el-icon class="el-icon--left" v-else><Upload /></el-icon>
            {{ hasImage && detectionResult ? t('detection.detectionComplete') : t('detection.waitingForUpload') }}
          </el-tag>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button
            :class="{ active: compareMode === 'side' }"
            size="small"
            @click="compareMode = 'side'"
          >
            <el-icon><Minus /></el-icon>
            {{ t('detection.sideBySide') }}
          </el-button>
          <el-button
            :class="{ active: compareMode === 'grid' }"
            size="small"
            @click="compareMode = 'grid'"
          >
            <el-icon><Grid /></el-icon>
            {{ t('detection.gridCompare') }}
          </el-button>
        </div>

        <!-- 摄像头实时检测 -->
        <div v-if="activeTab === 'camera'" class="camera-area">
          <CameraDetection @detect="handleCameraDetect" />
        </div>

        <!-- 图片对比区域 -->
        <div v-else class="image-compare" :class="compareMode">
          <div class="image-card">
            <input
              type="file"
              accept="image/*"
              class="hidden-file-input"
              ref="placeholderFileInput"
              @change="handlePlaceholderUpload($event)"
            />
            <template v-if="hasImage && originalImage">
              <el-image
                :src="originalImage"
                :alt="t('detection.originalImage')"
                class="compare-image"
                :preview-src-list="previewImages"
                :initial-index="0"
              />
            </template>
            <template v-else>
              <div class="image-placeholder" @click="triggerPlaceholderUpload">
                <el-icon class="placeholder-icon"><Upload /></el-icon>
                <p class="placeholder-text">{{ t('detection.uploadImage') }}</p>
                <p class="placeholder-desc">{{ t('detection.uploadTip') }}</p>
              </div>
            </template>
            <div class="image-label">{{ t('detection.originalImage') }}</div>
          </div>
          <div class="image-card">
            <template v-if="hasImage && resultImage">
              <el-image
                :src="resultImage"
                :alt="t('detection.detectionResult')"
                class="compare-image"
                :preview-src-list="previewImages"
                :initial-index="1"
              />
              <div class="detection-mark" v-if="detectionResult"></div>
            </template>
            <template v-else>
              <div class="image-placeholder">
                <el-icon class="placeholder-icon"><View /></el-icon>
                <p class="placeholder-text">{{ t('detection.resultWillShowHere') }}</p>
                <p class="placeholder-desc">{{ t('detection.uploadToStartDetection') }}</p>
              </div>
            </template>
            <div class="image-label">{{ t('detection.detectionResult') }}</div>
          </div>
        </div>
      </div>

      <!-- 右侧信息面板 -->
      <div class="right-panel">
        <!-- 模型信息 -->
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">{{ t('detection.detectionModel') }}</span>
            <span class="info-value">{{ selectedModel }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('detection.modelVersion') }}</span>
            <span class="info-value">v1.0.0</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('detection.detectionTarget') }}</span>
            <span class="info-value">{{ detectionResult?.total_objects || 0 }} {{ t('common.unit') || '' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('detection.detectionTime') }}</span>
            <span class="info-value">{{ detectionResult ? detectionResult.detection_time.toFixed(2) + 's' : '--' }}</span>
          </div>
        </div>

        <!-- 识别清单 -->
        <div class="result-card">
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span class="card-title">{{ t('detection.detectionList') }}</span>
            <el-tag v-if="detectionResult && detectionResult.total_objects > 0" size="small" type="success" effect="plain" round>
              {{ detectionResult.total_objects }} {{ t('detection.targetUnit') }}
            </el-tag>
          </div>
          <div v-if="!hasImage" class="empty-state">
            <el-icon class="empty-icon"><Upload /></el-icon>
            <p class="empty-text">{{ t('detection.pleaseUploadToStart') }}</p>
            <p class="empty-desc">{{ t('detection.uploadToDetect') }}</p>
          </div>
          <div
            v-else-if="!detectionResult || detectionResult.total_objects === 0"
            class="empty-state"
          >
            <el-icon class="empty-icon"><CircleCheck /></el-icon>
            <p class="empty-text">{{ t('detection.noTargetDetected') }}</p>
            <p class="empty-desc">{{ t('detection.noAnomalyInImage') }}</p>
          </div>
          <div v-else class="detection-list">
            <div
              v-for="(box, index) in detectionResult.boxes"
              :key="index"
              class="detection-item"
              :style="{ borderLeftColor: getConfidenceColor(box.confidence) }"
            >
              <div class="item-header">
                <span class="item-rank">#{{ index + 1 }}</span>
                <div class="item-name-group">
                  <span class="item-name-cn">{{ getChineseName(box) }}</span>
                  <span class="item-name-en">{{ box.class_name }}</span>
                </div>
                <span class="item-confidence" :style="{ color: getConfidenceColor(box.confidence) }">
                  {{ (box.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="confidence-bar-wrap">
                <div
                  class="confidence-bar-fill"
                  :style="{
                    width: (box.confidence * 100).toFixed(1) + '%',
                    backgroundColor: getConfidenceColor(box.confidence)
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI诊断建议 -->
        <div class="result-card">
          <div class="card-header">
            <el-icon><ChatDotRound /></el-icon>
            <span class="card-title">{{ t('detection.aiDiagnosisSuggestion') }}</span>
          </div>
          <div class="diagnosis-content">
            <p v-if="!hasImage">{{ t('detection.uploadToGenerateSuggestion') }}</p>
            <p v-else-if="!detectionResult">{{ t('detection.noTargetSpecified') }}</p>
            <div v-else>
              <p>{{ t('detection.detectedTargets', { count: detectionResult.total_objects, time: detectionResult.detection_time.toFixed(2) }) }}</p>
              <p class="mt-2">{{ t('detection.hereAreSuggestions') }}</p>
              <ul class="suggestions-list">
                <li v-for="(box, index) in detectionResult.boxes" :key="index">
                  <strong>{{ getChineseName(box) }}</strong>：{{ getSuggestion(box) }}
                </li>
              </ul>
              <p class="ai-disclaimer mt-3">{{ t('detection.aiPoweredAdvice') }}</p>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            size="default"
            class="btn-secondary"
            @click="handleRedetect"
            :disabled="!hasImage"
          >
            <el-icon><Refresh /></el-icon>
            {{ t('detection.reDetect') }}
          </el-button>
          <el-button type="primary" size="default" class="btn-primary" :disabled="!detectionResult">
            <el-icon><Download /></el-icon>
            {{ t('detection.exportReport') }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage, ElLoading } from "element-plus";
import CameraDetection from "../components/CameraDetection.vue";
import {
  Picture,
  Plus,
  FolderOpened,
  Monitor,
  Upload,
  View,
  Minus,
  Grid,
  List,
  CircleCheck,
  ChatDotRound,
  Refresh,
  Download,
} from "@element-plus/icons-vue";

const { t } = useI18n();

const selectedModel = ref("agri-pest-yolo11n");
const activeTab = ref("single");
const compareMode = ref("side");
const originalImage = ref(null);
const resultImage = ref(null);
const detectionResult = ref(null);
const isDetecting = ref(false);
const hasImage = ref(false);
const fileInputs = ref([]);
const placeholderFileInput = ref(null);

const previewImages = computed(() => {
  const images = [];
  if (originalImage.value) {
    images.push(originalImage.value);
  }
  if (resultImage.value) {
    images.push(resultImage.value);
  }
  return images;
});

const functionTabs = [
  {
    key: "single",
    icon: Picture,
    accept: "image/*",
    multiple: false,
  },
  {
    key: "batch",
    icon: Plus,
    accept: "image/*",
    multiple: true,
  },
  {
    key: "camera",
    icon: Monitor,
    accept: "image/*",
    multiple: false,
  },
  {
    key: "video",
    icon: FolderOpened,
    accept: "video/*",
    multiple: false,
  },
];

// 获取类别中文名（优先使用后端返回的chinese_name）
const getChineseName = (box) => {
  return box.chinese_name || box.class_name || '';
};

// 根据置信度获取颜色：红(低) → 橙(中) → 绿(高)
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#22c55e';
  if (confidence >= 0.5) return '#eab308';
  return '#ef4444';
};

const getSuggestion = (box) => {
  return box.treatment_advice || t('detection.defaultSuggestion');
};

onMounted(() => {});

const handleTabClick = (key) => {
  activeTab.value = key;
};

const handleCameraDetect = (data) => {
  hasImage.value = true;
  detectionResult.value = {
    boxes: data.boxes || [],
    total_objects: data.total_objects || 0,
    detection_time: data.detection_time || 0,
    model_name: selectedModel.value,
  };
};

const handleFileChange = async (event, tabKey) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    if (tabKey === "single") {
      await performSingleDetection(files[0]);
    } else if (tabKey === "batch") {
      await performBatchDetection(Array.from(files));
    } else if (tabKey === "video") {
      handleVideoUpload(files[0]);
    }
  }
  event.target.value = "";
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({
    lock: true,
    text: t('detection.detecting'),
    background: "rgba(0, 0, 0, 0.7)",
  });

  try {
    isDetecting.value = true;
    hasImage.value = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);

    const response = await fetch("/api/detection/single", {
      method: "POST",
      body: formData,
    });
    
    const result = await response.json();
    
    if (result.success && result.data) {
      detectionResult.value = result.data;
      originalImage.value = result.data.image_url;
      resultImage.value = result.data.result_image_url;
      ElMessage.success(t('detection.detectionSuccess'));
    } else {
      ElMessage.error(result.message || t('detection.detectionFailed'));
    }
  } catch (error) {
    console.error('Detection error:', error);
    ElMessage.error(t('detection.pleaseRetryLater'));
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const performBatchDetection = async (files) => {
  ElMessage.info(t('detection.startBatchDetection', { count: files.length }));
  
  for (let i = 0; i < files.length; i++) {
    await performSingleDetection(files[i]);
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  ElMessage.success(t('detection.batchDetectionComplete', { count: files.length }));
};

const handleVideoUpload = (file) => {
  ElMessage.info(t('detection.videoFeatureInDevelopment'));
};

const triggerPlaceholderUpload = () => {
  if (placeholderFileInput.value) {
    placeholderFileInput.value.click();
  }
};

const handlePlaceholderUpload = async (event) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    await performSingleDetection(files[0]);
  }
  event.target.value = "";
};

const handleRedetect = () => {
  if (fileInputs.value[0]) {
    fileInputs.value[0].click();
  }
};
</script>

<style scoped>
.detection-page {
  width: 100%;
  position: relative;
}

.page-header {
  margin-bottom: 32px;
  padding-top: 0;
}

.breadcrumb {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.separator {
  margin: 0 6px;
}

.active {
  color: var(--text-primary);
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 功能选项卡 */
.function-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.function-tab {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.function-tab:hover {
  background-color: var(--primary-light);
}

.function-tab.active {
  background-color: var(--primary-light);
  border-color: var(--primary-color);
}

.tab-icon {
  font-size: 18px;
  color: var(--primary-color);
  margin-right: 12px;
  flex-shrink: 0;
}

.tab-content {
  display: flex;
  flex-direction: column;
}

.tab-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}

.tab-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* 主内容区域 */
.main-content {
  display: flex;
  gap: 24px;
}

.left-panel {
  flex: 1;
  background-color: #ffffff;
  border-radius: 12px;
  padding: 20px;
}

.camera-area {
  width: 100%;
  min-height: 400px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.toolbar .el-button {
  border-radius: 6px;
  padding: 6px 14px;
}

.toolbar .el-button.active {
  background-color: var(--primary-light);
  color: var(--primary-color);
  border-color: var(--primary-color);
}

/* 图片对比区域 */
.image-compare {
  display: flex;
  gap: 16px;
  height: 320px;
}

.image-compare.grid {
  flex-direction: column;
  height: auto;
}

.image-compare.grid .image-card {
  height: 200px;
}

.image-card {
  flex: 1;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background-color: #f9fafb;
}

.hidden-file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 5;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  padding: 24px;
  text-align: center;
  cursor: pointer;
}

.image-placeholder:hover {
  background-color: rgba(34, 197, 94, 0.05);
}

.placeholder-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.placeholder-desc {
  font-size: 12px;
  color: #9ca3af;
}

.compare-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.5);
  color: #ffffff;
  font-size: 13px;
}

.detection-mark {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detection-mark::after {
  content: "✓";
  color: #ffffff;
  font-size: 18px;
  font-weight: bold;
}

/* 右侧面板 */
.right-panel {
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.result-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.card-header .el-icon {
  font-size: 16px;
  color: var(--primary-color);
  margin-right: 8px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
}

.empty-icon {
  font-size: 48px;
  color: var(--success-color);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.empty-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.diagnosis-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.diagnosis-content .mt-2 {
  margin-top: 8px;
}

.suggestions-list {
  margin-top: 8px;
  padding-left: 16px;
}

.suggestions-list li {
  margin-bottom: 8px;
  font-size: 12px;
}

.ai-disclaimer {
  font-size: 11px;
  color: var(--text-tertiary, #999);
  font-style: italic;
  border-top: 1px solid var(--border-light, #e8e8e8);
  padding-top: 10px;
  margin-top: 10px;
}

.detection-list {
  max-height: 300px;
  overflow-y: auto;
}

.detection-item {
  padding: 10px 14px;
  background-color: #fafbfc;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 3px solid #e5e7eb;
  transition: all 0.2s;
}

.detection-item:hover {
  background-color: #f0fdf4;
  transform: translateX(2px);
}

.detection-item:last-child {
  margin-bottom: 0;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.item-rank {
  font-size: 11px;
  font-weight: 700;
  color: #9ca3af;
  min-width: 22px;
  text-align: center;
}

.item-name-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-name-cn {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.item-name-en {
  font-size: 11px;
  color: #9ca3af;
  line-height: 1.3;
  word-break: break-all;
}

.item-confidence {
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
  margin-left: 4px;
}

.confidence-bar-wrap {
  height: 4px;
  background-color: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.confidence-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-secondary {
  flex: 1;
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
}

.btn-primary {
  flex: 2;
  border-radius: 8px;
  padding: 10px;
  font-size: 14px;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
}
</style>
