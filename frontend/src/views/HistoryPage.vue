<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">{{ t('history.title') }}</h1>
      <p class="page-subtitle">{{ t('history.subtitle') }}</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        :placeholder="t('history.searchPlaceholder')"
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="filterStatus"
        :placeholder="t('history.filterStatus')"
        size="default"
        class="filter-select"
      >
        <el-option :label="t('history.filterAll')" value="" />
        <el-option :label="t('history.statusCompleted')" value="completed" />
        <el-option :label="t('history.statusProcessing')" value="processing" />
        <el-option :label="t('history.statusFailed')" value="failed" />
      </el-select>

      <el-select
        v-model="filterType"
        :placeholder="t('history.filterType')"
        size="default"
        class="filter-select"
      >
        <el-option :label="t('history.filterAll')" value="" />
        <el-option :label="t('history.typeSingle')" value="single" />
        <el-option :label="t('history.typeBatch')" value="batch" />
        <el-option :label="t('history.typeFolder')" value="folder" />
        <el-option :label="t('history.typeVideo')" value="video" />
      </el-select>
    </div>

    <!-- 记录列表 -->
    <div class="history-list">
      <div
        v-for="record in displayRecords"
        :key="record.id"
        class="history-card"
      >
        <div class="record-preview" @click="viewRecord(record)">
          <img
            :src="record.result_image_url || record.image_url"
            :alt="record.filename"
            class="preview-image"
          />
          <div
            class="status-badge"
            :class="record.status"
          >
            <el-icon><component :is="getStatusIcon(record.status)" /></el-icon>
            {{ getStatusText(record.status) }}
          </div>
        </div>

        <div class="record-info" @click="viewRecord(record)">
          <div class="record-header">
            <span class="record-filename">{{ record.filename }}</span>
            <span class="record-type">{{ getTypeText(record.type) }}</span>
          </div>
          <div class="record-meta">
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ record.time }}
            </span>
            <span class="meta-item">
              <el-icon><Picture /></el-icon>
              {{ record.count || 1 }} {{ t('history.images') }}
            </span>
            <span class="meta-item">
              <el-icon><Aim /></el-icon>
              {{ record.total_objects }} {{ t('history.targets') }}
            </span>
          </div>
          <div class="record-tags">
            <span
              v-for="tag in record.detectedTargets"
              :key="tag"
              class="detected-tag"
            >
              {{ tag }}
            </span>
          </div>
        </div>

        <div class="record-actions">
          <el-button size="small" @click="viewRecord(record)">
            <el-icon><Monitor/></el-icon>
            {{ t('history.view') }}
          </el-button>
          <el-button size="small" @click="downloadRecord(record)">
            <el-icon><Download/></el-icon>
            {{ t('history.download') }}
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click="deleteRecord(record)"
          >
            <el-icon><Delete/></el-icon>
            {{ t('history.delete') }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="displayRecords.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Help /></el-icon>
      <p class="empty-text">{{ t('history.noRecords') }}</p>
      <el-button type="primary" @click="goToDetection">
        <el-icon><Plus /></el-icon>
        {{ t('history.startDetection') }}
      </el-button>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-if="totalRecords > 0"
        :total="totalRecords"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        layout="prev, pager, next"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Clock,
  Picture,
  Aim,
  Monitor,
  Download,
  Delete,
  Plus,
  Help,
  CircleCheck,
  Loading,
  CircleClose,
} from "@element-plus/icons-vue";

const router = useRouter();
const { t } = useI18n();

const searchQuery = ref("");
const filterStatus = ref("");
const filterType = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const isLoading = ref(false);

const historyRecords = ref([]);
const totalRecords = ref(0);

// 从localStorage获取用户信息
const getUserInfo = () => {
  const userStr = localStorage.getItem("user");
  if (userStr) {
    return JSON.parse(userStr);
  }
  return null;
};

// 获取检测历史
const fetchHistory = async () => {
  isLoading.value = true;
  try {
    const token = localStorage.getItem("token");
    const params = new URLSearchParams();
    params.append("page", String(currentPage.value));
    params.append("page_size", String(pageSize.value));
    
    const response = await fetch(`/api/detection/history?${params.toString()}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    const result = await response.json();
    
    if (result.success && result.data) {
      historyRecords.value = result.data.map(item => ({
        id: item.id,
        filename: item.filename,
        type: item.type || "single",
        status: item.status,
        time: item.time || formatDate(item.created_at),
        count: item.count || 1,
        total_objects: item.total_objects,
        image_url: item.image_url,
        result_image_url: item.result_image_url,
        detectedTargets: item.detected_targets || []
      }));
      totalRecords.value = result.total || result.data.length;
    } else {
      historyRecords.value = [];
      totalRecords.value = 0;
    }
  } catch (error) {
    console.error("获取检测历史失败:", error);
    ElMessage.error(t('history.fetchFailed'));
  } finally {
    isLoading.value = false;
  }
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const displayRecords = computed(() => {
  return historyRecords.value.filter((record) => {
    const matchesSearch =
      !searchQuery.value ||
      record.filename.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesStatus = !filterStatus.value || record.status === filterStatus.value;
    const matchesType = !filterType.value || record.type === filterType.value;
    return matchesSearch && matchesStatus && matchesType;
  });
});

const getStatusIcon = (status) => {
  const icons = {
    completed: CircleCheck,
    processing: Loading,
    failed: CircleClose,
  };
  return icons[status] || CircleCheck;
};

const getStatusText = (status) => {
  const texts = {
    completed: t('history.statusCompleted'),
    processing: t('history.statusProcessing'),
    failed: t('history.statusFailed'),
  };
  return texts[status] || status;
};

const getTypeText = (type) => {
  const texts = {
    single: t('history.typeSingle'),
    batch: t('history.typeBatch'),
    folder: t('history.typeFolder'),
    video: t('history.typeVideo'),
  };
  return texts[type] || type;
};

const viewRecord = (record) => {
  ElMessage.info(`${t('history.view')}: ${record.filename}`);
};

const downloadRecord = (record) => {
  ElMessage.info(`${t('history.download')}: ${record.filename}`);
};

const deleteRecord = async (record) => {
  try {
    await ElMessageBox.confirm(
      t('history.deleteConfirm', { filename: record.filename }),
      t('history.hint'),
      {
        confirmButtonText: t('history.confirm'),
        cancelButtonText: t('history.cancel'),
        type: "warning"
      }
    );
    
    const user = getUserInfo();
    const userId = user ? user.id : null;
    
    const params = new URLSearchParams();
    if (userId) {
      params.append("user_id", userId);
    }
    
    const response = await fetch(`/api/detection/${record.id}?${params.toString()}`, {
      method: "DELETE"
    });
    
    const result = await response.json();
    
    if (result.success) {
      ElMessage.success(t('history.deleteSuccess'));
      // 重新获取数据
      await fetchHistory();
    } else {
      ElMessage.error(result.message || t('history.deleteFailed'));
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error("删除记录失败:", error);
      ElMessage.error(t('history.deleteFailed'));
    }
  }
};

const goToDetection = () => {
  router.push("/detection");
};

const handlePageChange = (page) => {
  currentPage.value = page;
};

// 页面加载时获取数据
onMounted(() => {
  fetchHistory();
});
</script>

<style scoped lang="scss">
.history-page {
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

  .search-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    align-items: center;

    .search-input {
      flex: 1;
      max-width: 300px;
    }

    .filter-select {
      width: 140px;
    }
  }

  .history-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .history-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: var(--card-shadow);
    display: flex;
    align-items: center;
    gap: 20px;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      transform: translateY(-2px);
    }

    .record-preview {
      position: relative;
      width: 120px;
      height: 80px;
      border-radius: 8px;
      overflow: hidden;
      cursor: pointer;

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .status-badge {
        position: absolute;
        bottom: 8px;
        left: 8px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 4px;

        &.completed {
          background-color: rgba(34, 197, 94, 0.9);
          color: white;
        }

        &.processing {
          background-color: rgba(59, 130, 246, 0.9);
          color: white;
        }

        &.failed {
          background-color: rgba(239, 68, 68, 0.9);
          color: white;
        }
      }
    }

    .record-info {
      flex: 1;
      min-width: 0;
      cursor: pointer;

      .record-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;

        .record-filename {
          font-size: 15px;
          font-weight: 500;
          color: var(--text-primary);
        }

        .record-type {
          padding: 3px 8px;
          background-color: #f3f4f6;
          border-radius: 4px;
          font-size: 12px;
          color: var(--text-secondary);
        }
      }

      .record-meta {
        display: flex;
        gap: 20px;
        margin-bottom: 10px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: var(--text-secondary);

          :deep(.el-icon) {
            font-size: 14px;
          }
        }
      }

      .record-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;

        .detected-tag {
          padding: 3px 8px;
          background-color: rgba(39, 174, 96, 0.1);
          color: #27ae60;
          border-radius: 4px;
          font-size: 12px;
        }
      }
    }

    .record-actions {
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 0;

    .empty-icon {
      color: #9ca3af;
      margin-bottom: 16px;
    }

    .empty-text {
      font-size: 15px;
      color: var(--text-secondary);
      margin-bottom: 24px;
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 32px;
  }
}
</style>
