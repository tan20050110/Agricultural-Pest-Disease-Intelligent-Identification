<template>
  <div class="register-container">
    <div class="register-bg-decoration">
      <div class="decoration-circle c1"></div>
      <div class="decoration-circle c2"></div>
      <div class="decoration-circle c3"></div>
      <div class="decoration-leaf l1"></div>
      <div class="decoration-leaf l2"></div>
      <div class="decoration-leaf l3"></div>
    </div>
    
    <div class="register-card">
      <div class="register-header">
        <div class="logo-icon">
          <el-icon :size="40" color="white"><Cherry /></el-icon>
        </div>
        <h1 class="register-title">{{ t('auth.registerTitle') }}</h1>
        <p class="register-subtitle">{{ t('auth.registerSubtitle') }}</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            :placeholder="t('auth.usernamePlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            type="email"
            :placeholder="t('auth.emailPlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            :placeholder="t('auth.passwordPlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            :placeholder="t('auth.confirmPasswordPlaceholder')"
            size="large"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item class="agree-terms">
          <el-checkbox v-model="registerForm.agree" />
          <span>我已阅读并同意</span>
          <a href="#" class="terms-link">《服务条款》</a>
          <span>和</span>
          <a href="#" class="terms-link">《隐私政策》</a>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" class="register-btn" @click="handleRegister">
            {{ t('auth.registerButton') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-link">
        <span>{{ t('auth.hasAccount') }}</span>
        <router-link to="/login">{{ t('auth.loginNow') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { User, Message, Lock, Cherry } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useUserStore } from "../stores/user";
import { register } from "../api/auth";

const { t } = useI18n();
const router = useRouter();
const userStore = useUserStore();

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  agree: false,
});

const registerRules = {
  username: [
    { required: true, message: t('auth.usernamePlaceholder'), trigger: "blur" },
    { min: 3, max: 20, message: t('auth.usernameLengthError'), trigger: "blur" },
    { pattern: /^[a-zA-Z0-9_]+$/, message: t('auth.usernameFormatError'), trigger: "blur" },
  ],
  email: [
    { required: true, message: t('auth.emailPlaceholder'), trigger: "blur" },
    { type: "email", message: t('auth.emailFormatError'), trigger: "blur" },
  ],
  password: [
    { required: true, message: t('auth.passwordPlaceholder'), trigger: "blur" },
    { min: 6, max: 30, message: t('auth.passwordLengthError'), trigger: "blur" },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: t('auth.passwordFormatError'), trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: t('auth.confirmPasswordPlaceholder'), trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error(t('auth.passwordMismatch')));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
  agree: [
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error(t('auth.agreeTerms')));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
};

const registerFormRef = ref(null);
const isSubmitting = ref(false);

const handleRegister = () => {
  registerFormRef.value.validate(async (valid) => {
    if (valid) {
      isSubmitting.value = true;
      try {
        const response = await register({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
        });
        if (response.success) {
          ElMessage.success(t('auth.registerSuccess'));
          setTimeout(() => {
            router.push("/login");
          }, 1500);
        } else {
          ElMessage.error(response.message || t('auth.registerFailed'));
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
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #bbf7d0 100%);
  position: relative;
  overflow: hidden;
}

.register-bg-decoration {
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

.register-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(34, 197, 94, 0.15);
  position: relative;
  z-index: 10;
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.register-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.register-form {
  margin-bottom: 24px;
}

.agree-terms {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}

.terms-link {
  color: #27ae60;
  margin: 0 4px;
}

.terms-link:hover {
  text-decoration: underline;
}

.register-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
}

.login-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.login-link a {
  color: #27ae60;
  margin-left: 4px;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
