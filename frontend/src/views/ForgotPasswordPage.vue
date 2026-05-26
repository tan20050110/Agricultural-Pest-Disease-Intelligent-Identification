<template>
  <div class="forgot-container">
    <div class="forgot-card">
      <div class="forgot-header">
        <div class="logo-icon">
          <el-icon :size="40" color="#27ae60"><Lock /></el-icon>
        </div>
        <h1 class="forgot-title">{{ t('auth.forgotTitlePage') }}</h1>
        <p class="forgot-subtitle">{{ t('auth.forgotSubtitlePage') }}</p>
      </div>

      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        class="forgot-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            type="email"
            :placeholder="t('auth.emailPlaceholder')"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" class="submit-btn" @click="handleSubmit">
            {{ t('auth.sendResetLink') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="back-link">
        <span>{{ t('auth.rememberPassword') }}</span>
        <router-link to="/login">{{ t('auth.backToLogin') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { Lock, Message } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const router = useRouter();

const forgotForm = reactive({
  email: "",
});

const forgotRules = {
  email: [
    { required: true, message: t('auth.emailPlaceholder'), trigger: "blur" },
    { type: "email", message: t('auth.emailFormatError'), trigger: "blur" },
  ],
};

const forgotFormRef = ref(null);

const handleSubmit = () => {
  forgotFormRef.value.validate((valid) => {
    if (valid) {

      ElMessage.success(t('auth.resetSuccess'));
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    }
  });
};
</script>

<style scoped>
.forgot-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.forgot-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.forgot-header {
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

.forgot-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.forgot-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.forgot-form {
  margin-bottom: 24px;
}

.submit-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
}

.back-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.back-link a {
  color: #27ae60;
  margin-left: 4px;
}

.back-link a:hover {
  text-decoration: underline;
}
</style>
