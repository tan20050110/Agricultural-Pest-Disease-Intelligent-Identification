<template>
  <div class="disease-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb">
        <span>{{ t('disease.workspace') }}</span>
        <span class="separator">›</span>
        <span class="active">{{ t('disease.title') }}</span>
      </div>
      <h1 class="page-title">{{ t('disease.pageTitle') }}</h1>
      <p class="page-subtitle">
        {{ t('disease.pageSubtitle') }}
      </p>
    </div>

    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="model-selector">
        <span class="selector-label">{{ t('disease.detectionModel') }}：</span>
        <el-tag type="success" effect="dark" size="large">
          <el-icon class="model-icon"><Cpu /></el-icon>
          ResNet50 · {{ t('disease.diseaseClassification') }}
        </el-tag>
      </div>
      <div class="class-count-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>{{ t('disease.supportsClassCount', { count: 39 }) }}</span>
      </div>
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
      <!-- 左侧：图片上传与预览 -->
      <div class="left-panel">
        <div class="panel-header">
          <span class="panel-title">{{ t('disease.detectionPreview') }}</span>
          <el-tag
            :type="hasImage && diseaseResult && activeTab !== 'camera' ? 'success' : 'info'"
            effect="light"
            class="result-tag"
          >
            <el-icon class="el-icon--left" v-if="hasImage && diseaseResult && activeTab !== 'camera'"><Check /></el-icon>
            <el-icon class="el-icon--left" v-else><Upload /></el-icon>
            {{ activeTab === 'camera' ? t('detection.camera') : (hasImage && diseaseResult ? t('disease.detectionComplete') : t('disease.waitingForUpload')) }}
          </el-tag>
        </div>

        <!-- 摄像头实时检测 -->
        <div v-if="activeTab === 'camera'" class="camera-area">
          <CameraDetection mode="disease" @detect="handleCameraDetect" />
        </div>

        <!-- 图片区域 -->
        <div v-else class="image-section">
          <div class="image-card">
            <input
              type="file"
              accept="image/*"
              class="hidden-file-input"
              ref="placeholderInput"
              @change="handlePlaceholderUpload"
            />
            <template v-if="hasImage && originalImage">
              <el-image
                :src="originalImage"
                :alt="t('disease.originalImage')"
                class="preview-image"
                :preview-src-list="[originalImage]"
              />
              <div class="image-overlay" v-if="diseaseResult">
                <div class="top-prediction-badge">
                  <div class="badge-crop">{{ diseaseResult.prediction.crop }}</div>
                  <div class="badge-name">{{ diseaseResult.prediction.chinese_name || diseaseResult.prediction.disease }}</div>
                  <div class="badge-confidence">{{ (diseaseResult.prediction.confidence * 100).toFixed(1) }}%</div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="image-placeholder" @click="triggerUpload">
                <el-icon class="placeholder-icon"><Picture /></el-icon>
                <p class="placeholder-text">{{ t('disease.clickOrDragToUpload') }}</p>
                <p class="placeholder-desc">{{ t('disease.supportsJpgPng') }}</p>
                <el-button type="primary" size="small" class="upload-btn">
                  <el-icon><Upload /></el-icon>
                  {{ t('disease.selectImage') }}
                </el-button>
              </div>
            </template>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="activeTab !== 'camera'" class="action-buttons">
          <el-button
            size="default"
            class="btn-reupload"
            @click="triggerUpload"
          >
            <el-icon><Refresh /></el-icon>
            {{ t('disease.reDetect') }}
          </el-button>
          <el-button type="primary" size="default" class="btn-primary" :disabled="!diseaseResult">
            <el-icon><Download /></el-icon>
            {{ t('disease.exportReport') }}
          </el-button>
        </div>
      </div>

      <!-- 右侧：识别结果面板 -->
      <div class="right-panel">
        <!-- 模型信息 -->
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">{{ t('disease.detectionModel') }}</span>
            <span class="info-value">ResNet50</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('disease.modelVersion') }}</span>
            <span class="info-value">v1.0.0</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('disease.detectionTime') }}</span>
            <span class="info-value">{{ diseaseResult ? diseaseResult.detection_time.toFixed(2) + 's' : '--' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('disease.totalClasses') }}</span>
            <span class="info-value">39</span>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!diseaseResult && !hasImage" class="result-card empty-card">
          <div class="empty-state">
            <el-icon class="empty-icon"><Upload /></el-icon>
            <p class="empty-text">{{ t('disease.pleaseUploadToStart') }}</p>
            <p class="empty-desc">{{ t('disease.autoRecognizeTip') }}</p>
          </div>
        </div>

        <!-- Top-1 预测结果卡片 -->
        <div v-if="diseaseResult" class="result-card top-result-card">
          <div class="card-header">
            <el-icon><Medal /></el-icon>
            <span class="card-title">{{ t('disease.topPrediction') }}</span>
            <el-tag type="success" effect="dark" size="small">
              {{ (diseaseResult.prediction.confidence * 100).toFixed(1) }}%
            </el-tag>
          </div>
          <div class="top-result-body">
            <div class="result-main">
              <div class="result-disease-name">
                {{ diseaseResult.prediction.chinese_name || diseaseResult.prediction.disease }}
              </div>
              <div class="result-disease-en">{{ diseaseResult.prediction.class_name }}</div>
            </div>
            <div class="result-meta">
              <div class="meta-item">
                <span class="meta-label">{{ t('disease.crop') }}</span>
                <el-tag size="small">{{ diseaseResult.prediction.crop }}</el-tag>
              </div>
              <div class="meta-item">
                <span class="meta-label">{{ t('disease.disease') }}</span>
                <el-tag type="danger" size="small">{{ diseaseResult.prediction.disease }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- Top-5 预测概率列表 -->
        <div v-if="diseaseResult" class="result-card">
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span class="card-title">{{ t('disease.top5Predictions') }}</span>
          </div>
          <div class="top5-list">
            <div
              v-for="(item, index) in diseaseResult.top5"
              :key="index"
              class="top5-item"
              :class="{ 'is-first': index === 0 }"
            >
              <div class="top5-rank">
                <span class="rank-badge" :class="getRankClass(index)">{{ index + 1 }}</span>
              </div>
              <div class="top5-info">
                <div class="top5-name">
                  {{ item.chinese_name || item.disease }}
                </div>
                <div class="top5-en">{{ item.class_name }}</div>
              </div>
              <div class="top5-confidence">
                <div class="top5-bar-wrap">
                  <div
                    class="top5-bar"
                    :style="{ width: (item.confidence * 100).toFixed(1) + '%' }"
                    :class="getBarClass(index)"
                  ></div>
                </div>
                <span class="top5-percent">{{ (item.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 诊断建议 -->
        <div v-if="diseaseResult" class="result-card">
          <div class="card-header">
            <el-icon><ChatDotRound /></el-icon>
            <span class="card-title">{{ t('disease.aiDiagnosisSuggestion') }}</span>
          </div>
          <div class="diagnosis-content">
            <p>{{ t('disease.diagnosisResult', {
              disease: diseaseResult.prediction.chinese_name || diseaseResult.prediction.disease,
              confidence: (diseaseResult.prediction.confidence * 100).toFixed(1),
              time: diseaseResult.detection_time.toFixed(2)
            }) }}</p>
            <p class="mt-2">{{ t('disease.hereAreSuggestions') }}</p>
            <ul class="suggestions-list">
              <li>{{ getDiseaseSuggestion(diseaseResult.prediction) }}</li>
            </ul>
            <p class="ai-disclaimer mt-3">{{ t('disease.aiPoweredAdvice') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage, ElLoading } from "element-plus";
import {
  Picture,
  Plus,
  FolderOpened,
  Monitor,
  Upload,
  Check,
  Refresh,
  Download,
  Cpu,
  InfoFilled,
  Medal,
  List,
  ChatDotRound,
} from "@element-plus/icons-vue";
import CameraDetection from "../components/CameraDetection.vue";

const { t } = useI18n();

const activeTab = ref("single");
const originalImage = ref(null);
const diseaseResult = ref(null);
const isDetecting = ref(false);
const hasImage = ref(false);
const fileInputs = ref([]);
const placeholderInput = ref(null);

const functionTabs = [
  { key: "single",    icon: Picture,       accept: "image/*", multiple: false },
  { key: "batch",     icon: Plus,          accept: "image/*", multiple: true  },
  { key: "camera",    icon: Monitor,       accept: "image/*", multiple: false },
  { key: "video",     icon: FolderOpened,  accept: "video/*", multiple: false },
];

// 病害防治建议映射
const diseaseSuggestions = {
  "Apple_scab": "苹果痂病防治：1.清除落叶和病果；2.在萌芽前喷洒波尔多液；3.生长期可使用戊唑醇、苯醚甲环唑等杀菌剂。",
  "Apple_black_rot": "苹果黑腐病防治：1.修剪病枝并销毁；2.合理施肥增强树势；3.使用甲基硫菌灵、多菌灵等药剂。",
  "Apple_cedar_apple_rust": "苹果锈病防治：1.铲除转主寄主（桧柏）；2.萌芽前喷波尔多液；3.发病初期用三唑酮、戊唑醇等药剂。",
  "Apple_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Blueberry_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Cherry_Powdery_mildew": "樱桃白粉病防治：1.合理修剪保持通风透光；2.增施有机肥提高抗病力；3.使用硫磺制剂或三唑类杀菌剂。",
  "Cherry_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Corn_Cercospora_leaf_spot": "玉米灰斑病防治：1.选用抗病品种；2.合理密植；3.发病初期喷施丙环唑或苯醚甲环唑。",
  "Corn_Common_rust": "玉米锈病防治：1.选用抗锈病品种；2.合理施肥避免偏施氮肥；3.发病初期使用戊唑醇、氟环唑等药剂。",
  "Corn_Northern_Leaf_Blight": "玉米大斑病防治：1.选用抗病品种；2.清除田间病残体；3.发病初期喷施嘧菌酯、吡唑醚菌酯等。",
  "Corn_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Grape_Black_rot": "葡萄黑腐病防治：1.剪除病穗病枝；2.果穗套袋保护；3.使用嘧菌酯、吡唑醚菌酯等杀菌剂。",
  "Grape_Esca": "葡萄枝枯病防治：1.修剪病枝至健康部位；2.伤口涂抹杀菌剂保护；3.增强树势提高抗病力。",
  "Grape_Leaf_blight": "葡萄叶枯病防治：1.清除病叶并销毁；2.合理修剪保持通风；3.发病初期使用代森锰锌等保护性杀菌剂。",
  "Grape_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Orange_Haunglongbing": "柑橘黄龙病防治：1.严格检疫防止病菌传播；2.防治木虱传播媒介；3.及时挖除病株并销毁。",
  "Peach_Bacterial_spot": "桃细菌性穿孔病防治：1.选用抗病品种；2.增施有机肥；3.发病初期使用农用链霉素或氢氧化铜。",
  "Peach_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Pepper_bell_Bacterial_spot": "甜椒细菌性斑点病防治：1.种子消毒处理；2.轮作倒茬；3.发病初期使用铜制剂喷洒。",
  "Pepper_bell_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Potato_Early_blight": "马铃薯早疫病防治：1.选用抗病品种；2.适时早播；3.发病初期使用代森锰锌、嘧菌酯等药剂。",
  "Potato_Late_blight": "马铃薯晚疫病防治：1.选用抗病品种；2.及时发现并清除中心病株；3.预防性喷洒霜脲·锰锌等药剂。",
  "Potato_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Raspberry_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Soybean_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Squash_Powdery_mildew": "南瓜白粉病防治：1.合理密植保持通风；2.增施磷钾肥；3.使用硫磺制剂或三唑类杀菌剂。",
  "Strawberry_Leaf_scorch": "草莓叶枯病防治：1.清除老叶病叶；2.合理灌溉避免湿度过大；3.使用多菌灵或百菌清等药剂。",
  "Strawberry_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
  "Tomato_Bacterial_spot": "番茄细菌性斑点病防治：1.种子消毒；2.与非茄科作物轮作；3.发病初期喷洒氢氧化铜等铜制剂。",
  "Tomato_Early_blight": "番茄早疫病防治：1.轮作倒茬；2.合理施肥增施磷钾肥；3.使用代森锰锌或嘧菌酯等药剂。",
  "Tomato_Late_blight": "番茄晚疫病防治：1.选用抗病品种；2.加强田间通风；3.预防性喷洒霜脲·锰锌或氟啶胺等药剂。",
  "Tomato_Leaf_Mold": "番茄叶霉病防治：1.高温闷棚消毒；2.合理密植加强通风；3.使用多菌灵或甲基硫菌灵等药剂。",
  "Tomato_Septoria_leaf_spot": "番茄斑枯病防治：1.清除田间病残体；2.与非茄科作物轮作；3.初期喷洒百菌清或氢氧化铜。",
  "Tomato_Spider_mites": "番茄红蜘蛛防治：1.清除田间杂草；2.保护天敌；3.使用阿维菌素、哒螨灵等杀螨剂。",
  "Tomato_Target_Spot": "番茄斑点病防治：1.合理施肥增强植株抗性；2.及时摘除病叶；3.使用嘧菌酯等杀菌剂。",
  "Tomato_Tomato_Yellow_Leaf_Curl_Virus": "番茄黄化曲叶病毒病防治：1.防治烟粉虱传播媒介；2.选用抗病品种；3.拔除病株并销毁。",
  "Tomato_Tomato_mosaic_virus": "番茄花叶病毒病防治：1.选用无毒种子；2.防治蚜虫传播媒介；3.操作时注意消毒防止接触传播。",
  "Tomato_healthy": "叶片状态健康，无需特殊处理。继续保持良好的田间管理即可。",
};

const getDiseaseSuggestion = (prediction) => {
  // 优先使用后端返回的AI防治建议
  if (prediction.treatment_advice) {
    return prediction.treatment_advice;
  }
  // 兼容旧版API数据
  return diseaseSuggestions[prediction.disease] || t('disease.defaultSuggestion');
};

const getRankClass = (index) => {
  if (index === 0) return "rank-1";
  if (index === 1) return "rank-2";
  if (index === 2) return "rank-3";
  return "rank-other";
};

const getBarClass = (index) => {
  if (index === 0) return "bar-1";
  if (index === 1) return "bar-2";
  return "bar-other";
};

const handleTabClick = (key) => {
  activeTab.value = key;
  if (key === "video") ElMessage.info(t('detection.videoFeatureInDevelopment'));
};

const handleCameraDetect = (data) => {
  hasImage.value = true;
  const predictions = data.predictions || [];
  diseaseResult.value = {
    prediction: predictions[0] || {},
    top5: predictions,
    detection_time: data.detection_time || 0,
    model_name: "resnet50_disease",
  };
};

const triggerUpload = () => {
  if (fileInputs.value[0]) {
    fileInputs.value[0].click();
  }
};

const handlePlaceholderUpload = async (event) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    await performDiseaseDetection(files[0]);
  }
  event.target.value = "";
};

const handleFileChange = async (event, tabKey) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    if (tabKey === "single") {
      await performDiseaseDetection(files[0]);
    } else if (tabKey === "batch") {
      await performBatchDetection(Array.from(files));
    } else if (tabKey === "video") {
      ElMessage.info(t('detection.videoFeatureInDevelopment'));
    }
  }
  event.target.value = "";
};

const performDiseaseDetection = async (file) => {
  const loading = ElLoading.service({
    lock: true,
    text: t('disease.analyzing'),
    background: "rgba(0, 0, 0, 0.7)",
  });

  try {
    isDetecting.value = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", "resnet50_disease");

    const response = await fetch("/api/disease/single", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (result.success && result.data) {
      diseaseResult.value = result.data;
      originalImage.value = result.data.image_url;
      hasImage.value = true;
      ElMessage.success(t('disease.detectionSuccess'));
    } else {
      ElMessage.error(result.message || t('disease.detectionFailed'));
    }
  } catch (error) {
    console.error("Disease detection error:", error);
    ElMessage.error(t('disease.pleaseRetryLater'));
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const performBatchDetection = async (files) => {
  ElMessage.info(t('detection.startBatchDetection', { count: files.length }));
  for (let i = 0; i < files.length; i++) {
    await performDiseaseDetection(files[i]);
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  ElMessage.success(t('detection.batchDetectionComplete', { count: files.length }));
};
</script>

<style scoped>
.disease-page {
  width: 100%;
  position: relative;
}

.page-header {
  margin-bottom: 24px;
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

/* 顶部工具栏 */
.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: var(--card-shadow);
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selector-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.model-icon {
  margin-right: 4px;
}

.class-count-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.class-count-tip .el-icon {
  color: var(--primary-color);
}

/* 功能选项卡 */
.function-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.function-tab {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.function-tab:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.function-tab.active {
  border-color: var(--primary-color);
  background-color: rgba(34, 197, 94, 0.03);
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.tab-icon {
  color: var(--primary-color);
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tab-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.tab-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.camera-area {
  width: 100%;
  min-height: 400px;
}

/* 主内容区域 */
.main-content {
  display: flex;
  gap: 24px;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 0 20px;
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

.image-section {
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
}

.image-card {
  position: relative;
  min-height: 360px;
  background-color: #f9fafb;
  border-radius: 12px;
  overflow: hidden;
}

.hidden-file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 5;
}

.preview-image {
  width: 100%;
  min-height: 360px;
  object-fit: contain;
  display: block;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.top-prediction-badge {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 10px 18px;
  color: #ffffff;
}

.badge-crop {
  font-size: 11px;
  opacity: 0.75;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 2px;
}

.badge-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 2px;
}

.badge-confidence {
  font-size: 13px;
  color: #4ade80;
  font-weight: 500;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 360px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  transition: all 0.2s;
}

.image-placeholder:hover {
  border-color: var(--primary-color);
  background-color: rgba(34, 197, 94, 0.03);
}

.placeholder-icon {
  font-size: 56px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 6px;
}

.placeholder-desc {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 16px;
}

.upload-btn {
  border-radius: 8px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  padding: 0 20px 20px 20px;
  background-color: #ffffff;
  border-radius: 0 0 12px 12px;
}

.btn-reupload {
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

.btn-primary:disabled {
  opacity: 0.5;
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

/* 结果卡片 */
.result-card {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
}

.result-card.empty-card {
  flex: 1;
  display: flex;
  align-items: center;
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
  flex: 1;
}

/* Top-1 预测结果 */
.top-result-card {
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 50%, #dcfce7 100%);
  border: 1px solid #86efac;
}

.top-result-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-main {
  text-align: center;
  padding: 8px 0;
}

.result-disease-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.result-disease-en {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
}

.result-meta {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Top-5 列表 */
.top5-list {
  max-height: 280px;
  overflow-y: auto;
}

.top5-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.top5-item:hover {
  background-color: #f9fafb;
}

.top5-item.is-first {
  background-color: #f0fdf4;
}

.top5-rank {
  width: 28px;
  flex-shrink: 0;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  background-color: #e5e7eb;
  color: #6b7280;
}

.rank-badge.rank-1 {
  background-color: #22c55e;
  color: #ffffff;
}

.rank-badge.rank-2 {
  background-color: #eab308;
  color: #ffffff;
}

.rank-badge.rank-3 {
  background-color: #f97316;
  color: #ffffff;
}

.top5-info {
  flex: 1;
  min-width: 0;
}

.top5-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top5-en {
  font-size: 10px;
  color: var(--text-secondary);
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top5-confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 110px;
  flex-shrink: 0;
}

.top5-bar-wrap {
  flex: 1;
  height: 6px;
  background-color: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.top5-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.bar-1 {
  background-color: #22c55e;
}

.bar-2 {
  background-color: #eab308;
}

.bar-other {
  background-color: #9ca3af;
}

.top5-percent {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  width: 46px;
  text-align: right;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  width: 100%;
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

/* 诊断建议 */
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
</style>
