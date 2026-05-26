<template>
  <div class="qa-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('qa.title') }}</h1>
      <p class="page-subtitle">{{ t('qa.subtitle') }}</p>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="chatMessages">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message"
          :class="{ 'user-message': message.isUser }"
        >
          <div class="message-avatar">
            <el-icon><component :is="message.isUser ? User : Message" /></el-icon>
          </div>
          <div class="message-content">
            {{ message.content }}
          </div>
          <div class="message-time">{{ message.time }}</div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="question"
          :placeholder="t('qa.inputPlaceholder')"
          :rows="3"
          @keyup.enter="sendMessage"
        />
        <el-button type="primary" class="send-btn" :loading="sending" @click="sendMessage">
          <el-icon><ArrowRight /></el-icon>
          {{ t('qa.send') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { Message, User, ArrowRight } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const question = ref("");
const sending = ref(false);
const chatMessages = ref(null);

const messages = ref([
  {
    content: t('qa.welcomeMessage'),
    isUser: false,
    time: new Date().toLocaleTimeString()
  }
]);

const sendMessage = async () => {
  if (!question.value.trim() || sending.value) return;

  sending.value = true;
  const userQuestion = question.value.trim();
  
  // 添加用户消息
  messages.value.push({
    content: userQuestion,
    isUser: true,
    time: new Date().toLocaleTimeString()
  });
  
  question.value = "";
  
  // 滚动到底部
  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch("/api/qa/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `question=${encodeURIComponent(userQuestion)}`
    });
    
    const result = await response.json();
    
    if (result.success && result.data) {
      messages.value.push({
        content: result.data.answer,
        isUser: false,
        time: new Date().toLocaleTimeString()
      });
    } else {
      messages.value.push({
        content: t('qa.sorryCannotAnswer'),
        isUser: false,
        time: new Date().toLocaleTimeString()
      });
    }
  } catch (error) {
    console.error("发送消息失败:", error);
    ElMessage.error(t('qa.sendFailed'));
    messages.value.push({
      content: t('qa.networkError'),
      isUser: false,
      time: new Date().toLocaleTimeString()
    });
  } finally {
    sending.value = false;
    await nextTick();
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight;
  }
};
</script>

<style scoped lang="scss">
.qa-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

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

  .chat-container {
    flex: 1;
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: var(--card-shadow);
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;

      .message {
        display: flex;
        margin-bottom: 20px;
        align-items: flex-start;

        .message-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: var(--primary-color);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          flex-shrink: 0;

          :deep(.el-icon) {
            font-size: 18px;
          }
        }

        .message-content {
          background-color: #f3f4f6;
          padding: 12px 16px;
          border-radius: 0 12px 12px 12px;
          max-width: 70%;
          line-height: 1.6;
          font-size: 14px;
          color: var(--text-primary);
        }

        .message-time {
          font-size: 12px;
          color: #9ca3af;
          margin-left: 12px;
          margin-top: 4px;
          flex-shrink: 0;
        }

        &.user-message {
          flex-direction: row-reverse;

          .message-avatar {
            margin-right: 0;
            margin-left: 12px;
            background-color: #60a5fa;
          }

          .message-content {
            background-color: var(--primary-light);
            border-radius: 12px 0 12px 12px;
          }

          .message-time {
            margin-left: 0;
            margin-right: 12px;
          }
        }
      }
    }

    .chat-input {
      padding: 20px;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 12px;

      .send-btn {
        width: 100px;
        height: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }
    }
  }
}
</style>
