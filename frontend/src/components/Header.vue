<template>
  <div class="header-container">
    <div class="breadcrumbs">
      <el-icon class="breadcrumb-icon"><House /></el-icon>
      <span class="breadcrumb-separator">/</span>
      <span class="breadcrumb-text">{{ currentPageName }}</span>
    </div>

    <div class="header-actions">
      <el-tag type="success" effect="light" class="status-tag">
        <el-icon class="el-icon--left"><Check /></el-icon>
        {{ t('header.detectionComplete') }}
      </el-tag>

      <div class="action-icons">
        <el-icon class="action-icon"><Grid /></el-icon>
        <el-icon class="action-icon"><Bell /></el-icon>
        <el-icon class="action-icon"><QuestionFilled /></el-icon>
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="user-dropdown">
            <el-avatar class="user-avatar" size="32">
              <img
                src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
                :alt="t('header.avatarAlt')"
              />
            </el-avatar>
            <div class="user-info">
              <div class="user-name">{{ userStore.displayName }}</div>
              <div class="user-role">{{ t('header.userRole') }}</div>
            </div>
            <el-icon class="dropdown-icon"><CaretBottom /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">{{ t('header.profile') }}</el-dropdown-item>
              <el-dropdown-item command="logout" divided>{{ t('header.logout') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '../stores/user'
import {
  Check,
  Grid,
  Bell,
  QuestionFilled,
  CaretBottom,
  House,
} from "@element-plus/icons-vue";

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 根据当前路由获取对应的页面名称
const currentPageName = computed(() => {
  const pageMap = {
    '/detection': 'sidebar.smartDetection',
    '/history': 'sidebar.detectionHistory',
    '/qa': 'sidebar.agriculturalQA',
    '/targets': 'sidebar.pestLibrary',
    '/profile': 'sidebar.personalCenter',
    '/settings': 'sidebar.systemSettings'
  }
  return t(pageMap[route.path] || 'sidebar.smartDetection')
})

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

// 初始化用户信息
onMounted(() => {
  userStore.initUser()
})
</script>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.breadcrumbs {
  display: flex;
  align-items: center;
}

.breadcrumb-icon {
  font-size: 14px;
  color: var(--text-secondary);
}

.breadcrumb-separator {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 8px;
}

.breadcrumb-text {
  font-size: 14px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.status-tag {
  margin-right: 24px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
}

.action-icons {
  display: flex;
  align-items: center;
}

.action-icon {
  font-size: 18px;
  color: var(--text-secondary);
  margin-right: 20px;
  cursor: pointer;
  transition: color 0.2s;
}

.action-icon:hover {
  color: var(--primary-color);
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.user-dropdown:hover {
  background-color: #f3f4f6;
}

.user-avatar {
  margin-right: 8px;
}

.user-info {
  margin-right: 6px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 12px;
  margin-top: 5px;
  color: var(--text-secondary);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
