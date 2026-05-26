<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('profile.title') }}</h1>
      <p class="page-subtitle">{{ t('profile.subtitle') }}</p>
    </div>

    <div class="profile-content">
      <div class="user-info-card">
        <div class="user-avatar-section">
          <el-avatar size="80">
            <img
              src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
              :alt="t('profile.avatarAlt')"
            />
          </el-avatar>
          <div class="user-basic-info">
            <div class="user-name">{{ userInfo.nickname }}</div>
            <div class="user-role">{{ userInfo.role }}</div>
            <el-button
              size="small"
              type="primary"
              plain
              style="margin-top: 8px"
              @click="handleEditClick"
            >
              {{ t('profile.editProfile') }}
            </el-button>
          </div>
        </div>

        <div class="user-detail-info">
          <div class="info-item">
            <el-icon><Message /></el-icon>
            <span>{{ userInfo.email }}</span>
          </div>
          <div class="info-item">
            <el-icon><Calendar /></el-icon>
            <span>{{ t('profile.registeredAt') }}: {{ userInfo.created_at }}</span>
          </div>
        </div>
      </div>

      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.total_detections }}</div>
            <div class="stat-label">{{ t('profile.totalDetections') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Grid /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.total_targets }}</div>
            <div class="stat-label">{{ t('profile.totalTargets') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Cherry /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.success_rate }}%</div>
            <div class="stat-label">{{ t('profile.successRate') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.days_used }}</div>
            <div class="stat-label">{{ t('profile.usageDays') }}</div>
          </div>
        </div>
      </div>

      <div class="action-cards">
        <div class="action-card" @click="changePassword">
          <div class="action-icon">
            <el-icon><Lock /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">{{ t('profile.changePassword') }}</div>
            <div class="action-desc">{{ t('profile.changePasswordDesc') }}</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="action-card" @click="goToSettings">
          <div class="action-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">{{ t('profile.systemSettings') }}</div>
            <div class="action-desc">{{ t('profile.systemSettingsDesc') }}</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="action-card logout-card" @click="logout">
          <div class="action-icon logout-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="action-info">
            <div class="action-title">{{ t('profile.logout') }}</div>
            <div class="action-desc">{{ t('profile.logoutDesc') }}</div>
          </div>
          <el-icon class="action-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 编辑资料弹窗 -->
    <el-dialog
      :title="t('profile.editProfile')"
      :model-value="showEditModal"
      width="400px"
      @update:model-value="showEditModal = $event"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item :label="t('settings.nickname')">
          <el-input v-model="editForm.nickname" :placeholder="t('settings.nickname')" />
        </el-form-item>
        <el-form-item :label="t('settings.email')">
          <el-input v-model="editForm.email" :placeholder="t('settings.email')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditModal = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveEdit">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗 -->
    <el-dialog
      :title="t('profile.changePassword')"
      :model-value="showPwdModal"
      width="400px"
      @update:model-value="showPwdModal = $event"
    >
      <el-form :model="pwdForm" label-width="100px">
        <el-form-item :label="t('settings.oldPassword')">
          <el-input type="password" v-model="pwdForm.oldPassword" :placeholder="t('settings.oldPassword')" />
        </el-form-item>
        <el-form-item :label="t('settings.newPassword')">
          <el-input type="password" v-model="pwdForm.newPassword" :placeholder="t('settings.newPassword')" />
        </el-form-item>
        <el-form-item :label="t('settings.confirmPassword')">
          <el-input type="password" v-model="pwdForm.confirmPassword" :placeholder="t('settings.confirmPassword')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPwdModal = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="savePassword">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useUserStore } from "../stores/user";
import {
  Message,
  Calendar,
  CircleCheck,
  Grid,
  Cherry,
  Clock,
  Lock,
  User,
  CircleClose,
  ArrowRight
} from "@element-plus/icons-vue";

const { t } = useI18n();
const router = useRouter();
const userStore = useUserStore();

const showEditModal = ref(false);
const showPwdModal = ref(false);
const isLoading = ref(false);

// 使用 user store 中的用户信息
const userInfo = computed(() => userStore.userInfo);

// 本地统计数据保持
const userStats = reactive({
  total_detections: 128,
  total_targets: 892,
  success_rate: 98.5,
  days_used: 12
});

const editForm = reactive({
  nickname: "",
  email: ""
});

const pwdForm = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: ""
});

// 从localStorage获取用户信息
const getUserInfo = () => {
  const userStr = localStorage.getItem("user");
  if (userStr) {
    return JSON.parse(userStr);
  }
  return null;
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const userId = userStore.userInfo.id;
    
    const params = new URLSearchParams();
    if (userId) {
      params.append("user_id", userId);
    }
    
    const response = await fetch(`/api/user/info?${params.toString()}`);
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      
      // 更新用户 store
      userStore.updateUser({
        id: data.id,
        username: data.username,
        email: data.email,
        nickname: data.nickname,
        role: data.role,
        created_at: formatDate(data.created_at)
      });
      
      // 更新编辑表单
      editForm.nickname = data.nickname;
      editForm.email = data.email;
      
      // 更新统计数据
      if (data.stats) {
        userStats.total_detections = data.stats.total_detections;
        userStats.total_targets = data.stats.total_targets;
        userStats.success_rate = data.stats.success_rate;
        userStats.days_used = data.stats.days_used;
      }
    }
  } catch (error) {
    console.error("获取用户信息失败:", error);
  }
};

const handleEditClick = () => {
  // 先加载当前用户信息到表单
  editForm.nickname = userStore.userInfo.nickname;
  editForm.email = userStore.userInfo.email;
  showEditModal.value = true;
};

const saveEdit = async () => {
  if (!editForm.nickname && !editForm.email) {
    ElMessage.warning(t('profile.pleaseModifyAtLeastOne'));
    return;
  }
  
  isLoading.value = true;
  try {
    const userId = userStore.userInfo.id;
    
    const formData = new URLSearchParams();
    formData.append("user_id", userId);
    if (editForm.nickname) {
      formData.append("nickname", editForm.nickname);
    }
    if (editForm.email) {
      formData.append("email", editForm.email);
    }
    
    const response = await fetch("/api/user/update", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      // 更新用户 store（会自动同步到 localStorage）
      if (result.data) {
        userStore.updateUser(result.data);
      } else {
        userStore.updateUser({
          nickname: editForm.nickname,
          email: editForm.email
        });
      }
      
      showEditModal.value = false;
      ElMessage.success(t('profile.saveSuccess'));
    } else {
      ElMessage.error(result.message || t('profile.saveFailed'));
    }
  } catch (error) {
    console.error("更新用户信息失败:", error);
    ElMessage.error(t('profile.pleaseRetryLater'));
  } finally {
    isLoading.value = false;
  }
};

const changePassword = () => {
  showPwdModal.value = true;
};

const savePassword = async () => {
  if (!pwdForm.oldPassword) {
    ElMessage.warning(t('profile.pleaseEnterOldPassword'));
    return;
  }
  if (!pwdForm.newPassword) {
    ElMessage.warning(t('profile.pleaseEnterNewPassword'));
    return;
  }
  if (pwdForm.newPassword.length < 6) {
    ElMessage.warning(t('settings.passwordTooShort'));
    return;
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    ElMessage.warning(t('settings.passwordMismatch'));
    return;
  }
  
  try {
    const userId = userStore.userInfo.id;
    const formData = new URLSearchParams();
    formData.append("user_id", userId || "");
    formData.append("old_password", pwdForm.oldPassword);
    formData.append("new_password", pwdForm.newPassword);
    
    const response = await fetch("/api/user/change-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      showPwdModal.value = false;
      pwdForm.oldPassword = "";
      pwdForm.newPassword = "";
      pwdForm.confirmPassword = "";
      ElMessage.success(t('settings.passwordChangeSuccess'));
    } else {
      ElMessage.error(result.message || t('profile.saveFailed'));
    }
  } catch (error) {
    console.error("修改密码失败:", error);
    ElMessage.error(t('profile.pleaseRetryLater'));
  }
};

const goToSettings = () => {
  router.push("/settings");
};

const logout = () => {
  if (confirm(t('profile.logoutConfirm'))) {
    userStore.logout();
    router.push("/login");
  }
};

// 页面加载时获取数据
onMounted(() => {
  userStore.initUser(); // 确保从 localStorage 初始化用户信息
  
  // 如果 store 有数据，先同步到 editForm
  if (userStore.userInfo.nickname) {
    editForm.nickname = userStore.userInfo.nickname;
  }
  if (userStore.userInfo.email) {
    editForm.email = userStore.userInfo.email;
  }
  
  fetchUserInfo();
});

// 监听 store 中用户信息的变化，同步到 editForm
watch(() => [userStore.userInfo.nickname, userStore.userInfo.email], ([newNickname, newEmail]) => {
  if (newNickname) editForm.nickname = newNickname;
  if (newEmail) editForm.email = newEmail;
});
</script>

<style scoped lang="scss">
.profile-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .profile-content {
    display: flex;
    flex-direction: column;
    gap: 24px;

    .user-info-card {
      background-color: #ffffff;
      border-radius: 10px;
      padding: 24px;
      box-shadow: var(--card-shadow);

      .user-avatar-section {
        display: flex;
        align-items: center;

        .user-basic-info {
          margin-left: 24px;
          flex: 1;

          .user-name {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .user-role {
            font-size: 14px;
            color: var(--text-secondary);
          }
        }
      }

      .user-detail-info {
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px solid var(--border-color);
        display: flex;
        gap: 32px;

        .info-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--text-secondary);

          :deep(.el-icon) {
            font-size: 16px;
            color: var(--primary-color);
          }
        }
      }
    }

    .stats-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 24px;

      .stat-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: var(--card-shadow);

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          background-color: rgba(39, 174, 96, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;

          :deep(.el-icon) {
            font-size: 24px;
            color: #27ae60;
          }
        }

        .stat-content {
          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 13px;
            color: var(--text-secondary);
          }
        }
      }
    }

    .action-cards {
      display: flex;
      flex-direction: column;
      gap: 12px;

      .action-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: var(--card-shadow);

        &:hover {
          background-color: #f9fafb;
        }

        .action-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background-color: rgba(59, 130, 246, 0.1);
          display: flex;
          align-items: center;
          justify-content: center;

          :deep(.el-icon) {
            font-size: 20px;
            color: #3b82f6;
          }

          &.logout-icon {
            background-color: rgba(239, 68, 68, 0.1);

            :deep(.el-icon) {
              color: #ef4444;
            }
          }
        }

        .action-info {
          flex: 1;

          .action-title {
            font-size: 15px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .action-desc {
            font-size: 13px;
            color: var(--text-secondary);
          }
        }

        .action-arrow {
          color: #9ca3af;
        }

        &.logout-card {
          border-color: rgba(239, 68, 68, 0.2);
        }
      }
    }
  }
}
</style>
