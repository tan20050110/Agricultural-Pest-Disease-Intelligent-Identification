<template>
  <div class="sidebar-container">
    <div class="logo-section">
      <div class="logo-icon">
        <el-icon style="color: white; font-size: 22px"><Cherry /></el-icon>
      </div>
      <div class="logo-text">
        <div class="logo-title">{{ t('app.title') }}</div>
        <div class="logo-subtitle">{{ t('app.subtitle') }}</div>
      </div>
    </div>

    <div class="nav-menu">
      <div
        v-for="item in menuListWithLabels"
        :key="item.path"
        class="nav-item"
        :class="{ active: currentPath === item.path }"
        @click="handleMenuClick(item)"
      >
        <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
        <span class="nav-text">{{ item.label }}</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  Cherry,
  Search,
  Clock,
  Message,
  Folder,
  User,
  Setting,
  Apple,
  VideoCamera,
} from "@element-plus/icons-vue";

const { t } = useI18n();

const router = useRouter();
const route = useRoute();

const menuList = [
  {
    labelKey: "sidebar.pestDetection",
    icon: Search,
    path: "/detection",
  },
  {
    labelKey: "sidebar.diseaseRecognition",
    icon: Apple,
    path: "/disease",
  },
  {
    labelKey: "sidebar.detectionHistory",
    icon: Clock,
    path: "/history",
  },
  {
    labelKey: "sidebar.agriculturalQA",
    icon: Message,
    path: "/qa",
  },
  {
    labelKey: "sidebar.cameraDetection",
    icon: VideoCamera,
    path: "/camera",
  },
  {
    labelKey: "sidebar.pestLibrary",
    icon: Folder,
    path: "/targets",
  },
  {
    labelKey: "sidebar.personalCenter",
    icon: User,
    path: "/profile",
  },
  {
    labelKey: "sidebar.systemSettings",
    icon: Setting,
    path: "/settings",
  },
];

// 使用computed来实时翻译菜单项
const menuListWithLabels = computed(() => {
  return menuList.map(item => ({
    ...item,
    label: t(item.labelKey)
  }));
});

const currentPath = computed(() => route.path);

const handleMenuClick = (item) => {
  router.push(item.path);
};

</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-section {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  flex-shrink: 0;
}

.logo-text {
  overflow: hidden;
}

.logo-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.3;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  flex-direction: row;
  padding: 16px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: var(--primary-light);
}

.nav-item.active {
  background-color: var(--primary-light);
  border-left: 3px solid var(--primary-color);
  color: var(--primary-color);
  font-weight: 500;
}

.nav-item.active .nav-icon {
  color: var(--primary-color);
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.nav-text {
  font-size: 14px;
  line-height: 1.4;
}

</style>
