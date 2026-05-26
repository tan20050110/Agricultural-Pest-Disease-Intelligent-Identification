<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('settings.title') }}</h1>
      <p class="page-subtitle">管理系统配置和个人偏好设置</p>
    </div>

    <div class="settings-content">
      <div class="settings-section">
        <div class="section-header">
          <el-icon><User /></el-icon>
          <span class="section-title">{{ t('settings.accountSettings') }}</span>
        </div>
        <div class="settings-card">
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.username') }}</label>
            <div class="settings-value">{{ userInfo.username }}</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.nickname') }}</label>
            <div class="settings-value">{{ userInfo.nickname }}</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.email') }}</label>
            <div class="settings-value">{{ userInfo.email }}</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.role') }}</label>
            <div class="settings-value">{{ userInfo.role }}</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.registeredAt') }}</label>
            <div class="settings-value">{{ userInfo.created_at }}</div>
          </div>
          <div class="settings-actions">
            <el-button size="small" type="primary" plain @click="showPasswordModal">{{ t('settings.changePassword') }}</el-button>
            <el-button size="small" type="primary" @click="showEditModal">{{ t('settings.editProfile') }}</el-button>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-header">
          <el-icon><Bell /></el-icon>
          <span class="section-title">{{ t('settings.notificationSettings') }}</span>
        </div>
        <div class="settings-card">
          <div class="settings-item toggle-item">
            <div class="toggle-info">
              <label class="settings-label">{{ t('settings.detectionCompleteNotification') }}</label>
              <span class="settings-desc">{{ t('settings.detectionCompleteDesc') }}</span>
            </div>
            <el-switch v-model="notifications.detectionComplete" />
          </div>
          <div class="settings-item toggle-item">
            <div class="toggle-info">
              <label class="settings-label">{{ t('settings.systemUpdateNotification') }}</label>
              <span class="settings-desc">{{ t('settings.systemUpdateDesc') }}</span>
            </div>
            <el-switch v-model="notifications.systemUpdates" />
          </div>
          <div class="settings-item toggle-item">
            <div class="toggle-info">
              <label class="settings-label">{{ t('settings.emailNotification') }}</label>
              <span class="settings-desc">{{ t('settings.emailNotificationDesc') }}</span>
            </div>
            <el-switch v-model="notifications.emailNotifications" />
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-header">
          <el-icon><Cherry /></el-icon>
          <span class="section-title">{{ t('settings.appearanceSettings') }}</span>
        </div>
        <div class="settings-card">
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.themeMode') }}</label> &nbsp;
            <el-select v-model="appearance.theme" class="theme-select">
              <el-option :label="t('settings.lightMode')" value="light" />
              <el-option :label="t('settings.darkMode')" value="dark" />
              <el-option :label="t('settings.followSystem')" value="system" />
            </el-select>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.language') }}</label> &nbsp;
            <el-select v-model="appearance.language" class="language-select">
              <el-option :label="t('settings.chinese')" value="zh-CN" />
              <el-option :label="t('settings.english')" value="en-US" />
            </el-select>
          </div>
          <div class="settings-item toggle-item">
            <div class="toggle-info">
              <label class="settings-label">{{ t('settings.sidebarCollapsed') }}</label>
              <span class="settings-desc">{{ t('settings.sidebarCollapsedDesc') }}</span>
            </div>
            <el-switch v-model="appearance.sidebarCollapsed" />
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-header">
          <el-icon><Lock /></el-icon>
          <span class="section-title">{{ t('settings.securitySettings') }}</span>
        </div>
        <div class="settings-card">
          <div class="settings-item toggle-item">
            <div class="toggle-info">
              <label class="settings-label">{{ t('settings.twoFactorAuth') }}</label>
              <span class="settings-desc">{{ t('settings.twoFactorAuthDesc') }}</span>
            </div>
            <el-switch v-model="security.twoFactorAuth" />
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.sessionTimeout') }}</label> &nbsp;
            <el-select v-model="security.sessionTimeout" class="timeout-select">
              <el-option label="15分钟" value="15" />
              <el-option label="30分钟" value="30" />
              <el-option label="1小时" value="60" />
              <el-option label="2小时" value="120" />
              <el-option label="永不超时" value="0" />
            </el-select>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.loginRecords') }}</label>
            <div class="login-records">
              <div class="login-record">
                <span class="record-time">2024-01-20 14:30</span>
                <span class="record-ip">192.168.1.100</span>
                <span class="record-device">Windows Chrome</span>
              </div>
              <div class="login-record">
                <span class="record-time">2024-01-19 09:15</span>
                <span class="record-ip">192.168.1.100</span>
                <span class="record-device">Windows Chrome</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-header">
          <el-icon><Message /></el-icon>
          <span class="section-title">{{ t('settings.aboutSystem') }}</span>
        </div>
        <div class="settings-card">
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.systemName') }}</label>
            <div class="settings-value">农业病虫害智能识别系统</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.version') }}</label>
            <div class="settings-value">v1.0.0</div>
          </div>
          <div class="settings-item">
            <label class="settings-label">{{ t('settings.technicalSupport') }}</label>
            <div class="settings-value">support@agri-pest.com</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑资料弹窗 -->
    <el-dialog
      :title="t('settings.editProfile')"
      :model-value="showEditDialog"
      width="400px"
      @update:model-value="showEditDialog = $event"
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
        <el-button @click="showEditDialog = false">{{ t('settings.cancel') }}</el-button>
        <el-button type="primary" @click="saveEdit">{{ t('settings.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗 -->
    <el-dialog
      :title="t('settings.changePassword')"
      :model-value="showPwdDialog"
      width="400px"
      @update:model-value="showPwdDialog = $event"
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
        <el-button @click="showPwdDialog = false">{{ t('settings.cancel') }}</el-button>
        <el-button type="primary" @click="savePassword">{{ t('settings.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from "vue";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";
import { useUserStore } from "../stores/user";
import {
  User,
  Bell,
  Message,
  Lock,
  Cherry,
} from "@element-plus/icons-vue";

const { t, locale } = useI18n();
const userStore = useUserStore();

const showEditDialog = ref(false);
const showPwdDialog = ref(false);

// 使用 user store 中的用户信息
const userInfo = computed(() => userStore.userInfo);

const editForm = reactive({
  nickname: "",
  email: "",
});

const pwdForm = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const notifications = reactive({
  detectionComplete: true,
  systemUpdates: true,
  emailNotifications: false,
});

const appearance = reactive({
  theme: "light",
  language: "zh-CN",
  sidebarCollapsed: false,
});

const security = reactive({
  twoFactorAuth: false,
  sessionTimeout: "30",
});

// 从localStorage加载设置
const loadSettings = () => {
  try {
    const savedNotifications = localStorage.getItem("notifications");
    const savedAppearance = localStorage.getItem("appearance");
    const savedSecurity = localStorage.getItem("security");

    if (savedNotifications) {
      Object.assign(notifications, JSON.parse(savedNotifications));
    }
    if (savedAppearance) {
      Object.assign(appearance, JSON.parse(savedAppearance));
    }
    if (savedSecurity) {
      Object.assign(security, JSON.parse(savedSecurity));
    }
  } catch (error) {
    console.error("加载设置失败:", error);
  }
};

// 保存设置到localStorage
const saveSettings = () => {
  localStorage.setItem("notifications", JSON.stringify(notifications));
  localStorage.setItem("appearance", JSON.stringify(appearance));
  localStorage.setItem("security", JSON.stringify(security));
};

// 监听设置变化并保存
watch(notifications, saveSettings, { deep: true });
// 监听主题变化，只在真正改变时才触发
let previousTheme = appearance.theme;
let previousLanguage = appearance.language;
watch(appearance, (newVal) => {
  saveSettings();
  // 应用主题切换（只在主题真正改变时）
  if (newVal.theme !== previousTheme) {
    previousTheme = newVal.theme;
    applyTheme(newVal.theme, true); // 显示消息
  }
  // 应用语言切换（只在语言真正改变时）
  if (newVal.language !== previousLanguage && newVal.language !== locale.value) {
    previousLanguage = newVal.language;
    locale.value = newVal.language;
    ElMessage.success(`Language switched to ${newVal.language === 'zh-CN' ? '简体中文' : 'English'}`);
  }
}, { deep: true });
watch(security, saveSettings, { deep: true });

// 应用主题
const applyTheme = (theme, showMessage = false) => {
  const html = document.documentElement;
  html.classList.remove("light", "dark");
  let finalTheme = theme;
  
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    finalTheme = prefersDark ? "dark" : "light";
  }
  
  html.classList.add(finalTheme);
  // Element Plus暗色模式
  if (finalTheme === "dark") {
    html.classList.add("dark");
  } else {
    html.classList.remove("dark");
  }
  
  if (showMessage) {
    ElMessage.success(`已切换到${finalTheme === "light" ? "亮色模式" : "暗色模式"}`);
  }
};

// 从localStorage获取用户信息
const getUserInfo = () => {
  const userStr = localStorage.getItem("user");
  if (userStr) {
    return JSON.parse(userStr);
  }
  return null;
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
        created_at: data.created_at
      });

      // 更新编辑表单
      editForm.nickname = data.nickname;
      editForm.email = data.email;
    }
  } catch (error) {
    console.error("获取用户信息失败:", error);
  }
};

const showEditModal = () => {
  // 先加载当前用户信息到表单
  editForm.nickname = userStore.userInfo.nickname;
  editForm.email = userStore.userInfo.email;
  showEditDialog.value = true;
};

const saveEdit = async () => {
  if (!editForm.nickname && !editForm.email) {
    ElMessage.warning("请至少修改一项内容");
    return;
  }

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
      body: formData,
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

      showEditDialog.value = false;
      ElMessage.success("修改成功");
    } else {
      ElMessage.error(result.message || "修改失败");
    }
  } catch (error) {
    console.error("更新用户信息失败:", error);
    ElMessage.error("修改失败，请稍后重试");
  }
};

const showPasswordModal = () => {
  showPwdDialog.value = true;
};

const savePassword = () => {
  if (!pwdForm.oldPassword) {
    ElMessage.warning("请输入原密码");
    return;
  }
  if (!pwdForm.newPassword) {
    ElMessage.warning("请输入新密码");
    return;
  }
  if (pwdForm.newPassword.length < 6) {
    ElMessage.warning("新密码长度至少为6位");
    return;
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }

  showPwdDialog.value = false;
  pwdForm.oldPassword = "";
  pwdForm.newPassword = "";
  pwdForm.confirmPassword = "";
  ElMessage.success("密码修改成功");
};

// 页面加载时获取数据
onMounted(() => {
  loadSettings();
  
  // 更新 previousTheme 和 previousLanguage
  previousTheme = appearance.theme;
  previousLanguage = appearance.language;
  
  userStore.initUser(); // 确保从 localStorage 初始化用户信息
  
  // 如果 store 有数据，先同步到 editForm
  if (userStore.userInfo.nickname) {
    editForm.nickname = userStore.userInfo.nickname;
  }
  if (userStore.userInfo.email) {
    editForm.email = userStore.userInfo.email;
  }
  
  fetchUserInfo();
  applyTheme(appearance.theme, false); // 初始化时不显示消息
});

// 监听 store 中用户信息的变化，同步到 editForm
watch(() => [userStore.userInfo.nickname, userStore.userInfo.email], ([newNickname, newEmail]) => {
  if (newNickname) editForm.nickname = newNickname;
  if (newEmail) editForm.email = newEmail;
});
</script>

<style scoped lang="scss">
.settings-page {
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

  .settings-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .settings-section {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: var(--card-shadow);

    .section-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-color);

      .el-icon {
        font-size: 18px;
        color: var(--primary-color);
      }

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }

    .settings-card {
      .settings-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #f3f4f6;

        &:last-child {
          border-bottom: none;
        }

        &.toggle-item {
          .toggle-info {
            flex: 1;
          }
        }

        .settings-label {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        .settings-value {
          font-size: 14px;
          color: var(--text-primary);
          font-weight: 500;
        }

        .settings-desc {
          font-size: 12px;
          color: #9ca3af;
        }

        .theme-select,
        .language-select,
        .timeout-select {
          width: 180px;
        }

        .login-records {
          flex: 1;
          margin-left: 20px;

          .login-record {
            display: flex;
            gap: 20px;
            padding: 10px 0;
            font-size: 13px;
            color: var(--text-secondary);

            &:not(:last-child) {
              border-bottom: 1px dashed #e5e7eb;
            }
          }
        }
      }

      .settings-actions {
        display: flex;
        gap: 12px;
        padding-top: 16px;
      }
    }
  }
}
</style>