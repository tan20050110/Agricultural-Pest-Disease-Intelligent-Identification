<template>
  <div class="camera-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ t('camera.title') }}</h1>
        <p class="page-subtitle">{{ t('camera.subtitle') }}</p>
      </div>
    </div>

    <!-- 摄像头检测组件 -->
    <div class="camera-content">
      <CameraDetection />
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import CameraDetection from '../components/CameraDetection.vue'

const { t } = useI18n()
</script>

<style scoped>
.camera-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary, #64748b);
  margin: 0;
}

.camera-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
