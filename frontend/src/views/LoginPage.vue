<template>
  <div class="login-container">
    <div class="login-bg-decoration">
      <div class="decoration-circle c1"></div>
      <div class="decoration-circle c2"></div>
      <div class="decoration-circle c3"></div>
      <div class="decoration-leaf l1"></div>
      <div class="decoration-leaf l2"></div>
      <div class="decoration-leaf l3"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="40" color="white"><Cherry /></el-icon>
        </div>
        <h1 class="login-title">{{ t('app.title') }}</h1>
        <p class="login-subtitle">{{ t('app.subtitle') }}</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="t('auth.usernamePlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="t('auth.passwordPlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item class="form-actions">
          <el-checkbox v-model="loginForm.remember">{{ t('auth.rememberMe') }}</el-checkbox>
          <router-link to="/forgot-password" class="forgot-password">{{ t('auth.forgotPassword') }}?</router-link>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" @click="handleLogin">
            {{ t('auth.loginButton') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        <span>{{ t('auth.noAccount') }}</span>
        <router-link to="/register">{{ t('auth.registerNow') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { User, Lock, Cherry } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useUserStore } from "../stores/user";
import { login } from "../api/auth";

const { t } = useI18n();
const router = useRouter();
const userStore = useUserStore();

const loginForm = reactive({
  username: "",
  password: "",
  remember: false,
});

const loginRules = {
  username: [
    { required: true, message: t('auth.usernamePlaceholder'), trigger: "blur" },
    { min: 3, max: 20, message: t('auth.usernameLengthError'), trigger: "blur" },
  ],
  password: [
    { required: true, message: t('auth.passwordPlaceholder'), trigger: "blur" },
    { min: 6, max: 30, message: t('auth.passwordLengthError'), trigger: "blur" },
  ],
};

const loginFormRef = ref(null);
const isSubmitting = ref(false);

const handleLogin = () => {
  loginFormRef.value.validate(async (valid) => {
    if (valid) {
      isSubmitting.value = true;
      try {
        const response = await login({
          username: loginForm.username,
          password: loginForm.password,
        });
        if (response.success) {
          // 更新用户 store
          userStore.updateUser(response.user);
          localStorage.setItem("token", response.token);
          ElMessage.success(t('auth.loginSuccess'));
          router.push("/detection");
        } else {
          ElMessage.error(response.message || t('auth.loginFailed'));
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || t('auth.checkNetwork'));
      } finally {
        isSubmitting.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #bbf7d0 100%);
  position: relative;
  overflow: hidden;
}

.login-bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.decoration-circle.c1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #16a34a, #22c55e);
  top: -100px;
  right: -50px;
}

.decoration-circle.c2 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  bottom: -80px;
  left: -30px;
}

.decoration-circle.c3 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  top: 50%;
  left: -75px;
}

.decoration-leaf {
  position: absolute;
  opacity: 0.1;
  animation: float 6s ease-in-out infinite;
}

.decoration-leaf::before {
  content: "🍃";
  font-size: 48px;
}

.decoration-leaf.l1 {
  top: 20%;
  right: 15%;
  animation-delay: 0s;
}

.decoration-leaf.l2 {
  top: 60%;
  left: 20%;
  animation-delay: 2s;
}

.decoration-leaf.l3 {
  bottom: 25%;
  right: 30%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(5deg);
  }
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(34, 197, 94, 0.15);
  position: relative;
  z-index: 10;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.login-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.login-form {
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.forgot-password {
  font-size: 13px;
  color: #27ae60;
  cursor: pointer;
}

.forgot-password:hover {
  text-decoration: underline;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
}

.register-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.register-link a {
  color: #27ae60;
  margin-left: 4px;
  cursor: pointer;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>
