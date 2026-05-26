<template>
  <div class="targets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">{{ t('targets.title') }}</h1>
      <p class="page-subtitle">{{ t('targets.subtitle') }}</p>
    </div>

    <!-- 搜索框 -->
    <div class="search-container">
      <el-input
        v-model="searchQuery"
        :placeholder="t('targets.searchPlaceholder')"
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon target-icon">
          <el-icon><Aim /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ totalTargets }}</div>
          <div class="stat-label">{{ t('targets.totalTargets') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon category-icon">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ categories.length }}</div>
          <div class="stat-label">{{ t('targets.categoryCount') }}</div>
        </div>
      </div>
    </div>

    <!-- 目标类别列表 -->
    <div class="target-categories">
      <div
        v-for="category in filteredCategories"
        :key="category.id"
        class="category-card"
      >
        <div class="category-header">
          <div
            class="category-icon"
            :style="{ backgroundColor: category.color }"
          >
            <component :is="category.icon" />
          </div>
          <div class="category-info">
            <div class="category-name">{{ t(`targets.${category.nameKey}`) }}</div>
            <div class="category-count">
              {{ category.targets.length }} {{ t('targets.targetsCount') }}
            </div>
          </div>
        </div>
        <div class="target-list">
          <div
            v-for="target in category.targets"
            :key="target.id"
            class="target-item"
            @click="showTargetDetail(target)"
          >
            <el-icon :size="14" class="target-item-icon"><CircleCheck /></el-icon>
            <span>{{ t(`targets.${target.nameKey}`) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="filteredCategories.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Help /></el-icon>
      <p class="empty-text">{{ t('targets.emptyState') }}</p>
    </div>

    <!-- 目标详情弹窗 -->
    <el-dialog
      v-if="selectedTarget"
      :title="t(`targets.${selectedTarget.nameKey}`)"
      v-model="showDialog"
      width="400px"
    >
      <div class="target-detail">
        <div class="detail-icon" :style="{ backgroundColor: getCategoryColor(selectedTarget.categoryId) }">
          <el-icon :size="48"><component :is="getCategoryIcon(selectedTarget.categoryId)" /></el-icon>
        </div>
        <div class="detail-info">
          <div class="detail-item">
            <span class="detail-label">{{ t('targets.category') }}</span>
            <span class="detail-value">{{ getCategoryName(selectedTarget.categoryId) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ t('targets.crop') }}</span>
            <span class="detail-value">{{ getCategoryCrop(selectedTarget.categoryId) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ t('targets.description') }}</span>
            <span class="detail-value">{{ t(`targets.${selectedTarget.descKey}`) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ t('targets.harmLevel') }}</span>
            <span 
              class="detail-value harm-level"
              :class="selectedTarget.harmLevel?.toLowerCase()"
            >
              {{ getHarmLevelText(selectedTarget.harmLevel) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">{{ t('targets.accuracy') }}</span>
            <span class="detail-value">{{ selectedTarget.accuracy }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import {
  Search,
  Grid,
  Help,
  CircleCheck,
  Aim,
  User,
  Lock,
  Message,
  Cherry,
} from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const searchQuery = ref("");
const showDialog = ref(false);
const selectedTarget = ref(null);

const categories = ref([
  {
    id: 1,
    nameKey: "categoryRiceDisease",
    icon: Lock,
    color: "#ef4444",
    cropKey: "cropRice",
    targets: [
      { id: 1, nameKey: "riceBlast", categoryId: 1, descKey: "riceBlastDesc", accuracy: "98.5%", harmLevel: "高" },
      { id: 2, nameKey: "riceSheathBlight", categoryId: 1, descKey: "riceSheathBlightDesc", accuracy: "97.8%", harmLevel: "中" },
      { id: 3, nameKey: "riceBacterialLeafBlight", categoryId: 1, descKey: "riceBacterialLeafBlightDesc", accuracy: "96.2%", harmLevel: "高" },
      { id: 4, nameKey: "riceFalseSmut", categoryId: 1, descKey: "riceFalseSmutDesc", accuracy: "95.4%", harmLevel: "中" },
      { id: 5, nameKey: "riceBakanae", categoryId: 1, descKey: "riceBakanaeDesc", accuracy: "94.1%", harmLevel: "低" },
    ],
  },
  {
    id: 2,
    nameKey: "categoryWheatDisease",
    icon: Lock,
    color: "#dc2626",
    cropKey: "cropWheat",
    targets: [
      { id: 6, nameKey: "wheatStripeRust", categoryId: 2, descKey: "wheatStripeRustDesc", accuracy: "98.2%", harmLevel: "高" },
      { id: 7, nameKey: "wheatPowderyMildew", categoryId: 2, descKey: "wheatPowderyMildewDesc", accuracy: "97.5%", harmLevel: "中" },
      { id: 8, nameKey: "wheatHeadBlight", categoryId: 2, descKey: "wheatHeadBlightDesc", accuracy: "96.8%", harmLevel: "高" },
      { id: 9, nameKey: "wheatSheathBlight", categoryId: 2, descKey: "wheatSheathBlightDesc", accuracy: "95.3%", harmLevel: "中" },
      { id: 10, nameKey: "wheatLeafRust", categoryId: 2, descKey: "wheatLeafRustDesc", accuracy: "94.7%", harmLevel: "低" },
    ],
  },
  {
    id: 3,
    nameKey: "categoryCornDisease",
    icon: Lock,
    color: "#f59e0b",
    cropKey: "cropCorn",
    targets: [
      { id: 11, nameKey: "cornNorthernLeafBlight", categoryId: 3, descKey: "cornNorthernLeafBlightDesc", accuracy: "97.9%", harmLevel: "高" },
      { id: 12, nameKey: "cornSouthernLeafBlight", categoryId: 3, descKey: "cornSouthernLeafBlightDesc", accuracy: "96.6%", harmLevel: "中" },
      { id: 13, nameKey: "cornRust", categoryId: 3, descKey: "cornRustDesc", accuracy: "95.8%", harmLevel: "中" },
      { id: 14, nameKey: "cornSheathBlight", categoryId: 3, descKey: "cornSheathBlightDesc", accuracy: "94.2%", harmLevel: "低" },
      { id: 15, nameKey: "cornEarRot", categoryId: 3, descKey: "cornEarRotDesc", accuracy: "93.5%", harmLevel: "高" },
    ],
  },
  {
    id: 4,
    nameKey: "categoryVegetableDisease",
    icon: Lock,
    color: "#22c55e",
    cropKey: "cropVegetable",
    targets: [
      { id: 16, nameKey: "tomatoLateBlight", categoryId: 4, descKey: "tomatoLateBlightDesc", accuracy: "98.1%", harmLevel: "高" },
      { id: 17, nameKey: "cucumberDownyMildew", categoryId: 4, descKey: "cucumberDownyMildewDesc", accuracy: "97.3%", harmLevel: "高" },
      { id: 18, nameKey: "cabbageSoftRot", categoryId: 4, descKey: "cabbageSoftRotDesc", accuracy: "96.4%", harmLevel: "高" },
      { id: 19, nameKey: "pepperBlight", categoryId: 4, descKey: "pepperBlightDesc", accuracy: "95.7%", harmLevel: "中" },
      { id: 20, nameKey: "eggplantVerticilliumWilt", categoryId: 4, descKey: "eggplantVerticilliumWiltDesc", accuracy: "94.6%", harmLevel: "中" },
    ],
  },
  {
    id: 5,
    nameKey: "categoryRicePest",
    icon: User,
    color: "#f97316",
    cropKey: "cropRice",
    targets: [
      { id: 21, nameKey: "brownPlanthopper", categoryId: 5, descKey: "brownPlanthopperDesc", accuracy: "99.2%", harmLevel: "高" },
      { id: 22, nameKey: "stemBorer", categoryId: 5, descKey: "stemBorerDesc", accuracy: "98.5%", harmLevel: "高" },
      { id: 23, nameKey: "riceLeafroller", categoryId: 5, descKey: "riceLeafrollerDesc", accuracy: "97.8%", harmLevel: "中" },
      { id: 24, nameKey: "riceLeafhopper", categoryId: 5, descKey: "riceLeafhopperDesc", accuracy: "96.3%", harmLevel: "中" },
      { id: 25, nameKey: "riceWeevil", categoryId: 5, descKey: "riceWeevilDesc", accuracy: "95.1%", harmLevel: "低" },
    ],
  },
  {
    id: 6,
    nameKey: "categoryWheatPest",
    icon: User,
    color: "#ea580c",
    cropKey: "cropWheat",
    targets: [
      { id: 26, nameKey: "wheatAphid", categoryId: 6, descKey: "wheatAphidDesc", accuracy: "99.3%", harmLevel: "高" },
      { id: 27, nameKey: "wheatMidge", categoryId: 6, descKey: "wheatMidgeDesc", accuracy: "98.1%", harmLevel: "高" },
      { id: 28, nameKey: "wheatMite", categoryId: 6, descKey: "wheatMiteDesc", accuracy: "96.7%", harmLevel: "中" },
      { id: 29, nameKey: "wheatStemSawfly", categoryId: 6, descKey: "wheatStemSawflyDesc", accuracy: "95.4%", harmLevel: "低" },
      { id: 30, nameKey: "armyworm", categoryId: 6, descKey: "armywormDesc", accuracy: "94.8%", harmLevel: "高" },
    ],
  },
  {
    id: 7,
    nameKey: "categoryCornPest",
    icon: User,
    color: "#d97706",
    cropKey: "cropCorn",
    targets: [
      { id: 31, nameKey: "cornBorer", categoryId: 7, descKey: "cornBorerDesc", accuracy: "98.9%", harmLevel: "高" },
      { id: 32, nameKey: "cornAphid", categoryId: 7, descKey: "cornAphidDesc", accuracy: "97.6%", harmLevel: "中" },
      { id: 33, nameKey: "cornArmyworm", categoryId: 7, descKey: "cornArmywormDesc", accuracy: "96.2%", harmLevel: "高" },
      { id: 34, nameKey: "riceWeevilStored", categoryId: 7, descKey: "riceWeevilStoredDesc", accuracy: "95.5%", harmLevel: "低" },
      { id: 35, nameKey: "cottonBollworm", categoryId: 7, descKey: "cottonBollwormDesc", accuracy: "94.3%", harmLevel: "中" },
    ],
  },
  {
    id: 8,
    nameKey: "categoryVegetablePest",
    icon: User,
    color: "#fb923c",
    cropKey: "cropVegetable",
    targets: [
      { id: 36, nameKey: "cabbageWorm", categoryId: 8, descKey: "cabbageWormDesc", accuracy: "99.1%", harmLevel: "中" },
      { id: 37, nameKey: "diamondbackMoth", categoryId: 8, descKey: "diamondbackMothDesc", accuracy: "98.4%", harmLevel: "中" },
      { id: 38, nameKey: "vegetableAphid", categoryId: 8, descKey: "vegetableAphidDesc", accuracy: "97.9%", harmLevel: "高" },
      { id: 39, nameKey: "spiderMite", categoryId: 8, descKey: "spiderMiteDesc", accuracy: "96.8%", harmLevel: "中" },
      { id: 40, nameKey: "whitefly", categoryId: 8, descKey: "whiteflyDesc", accuracy: "95.6%", harmLevel: "中" },
    ],
  },
  {
    id: 9,
    nameKey: "categoryWeed",
    icon: Cherry,
    color: "#16a34a",
    cropKey: "cropGeneral",
    targets: [
      { id: 41, nameKey: "barnyardgrass", categoryId: 9, descKey: "barnyardgrassDesc", accuracy: "99.6%", harmLevel: "高" },
      { id: 42, nameKey: "chineseSprangletop", categoryId: 9, descKey: "chineseSprangletopDesc", accuracy: "98.8%", harmLevel: "高" },
      { id: 43, nameKey: "crabgrass", categoryId: 9, descKey: "crabgrassDesc", accuracy: "97.5%", harmLevel: "中" },
      { id: 44, nameKey: "greenFoxtail", categoryId: 9, descKey: "greenFoxtailDesc", accuracy: "96.3%", harmLevel: "中" },
      { id: 45, nameKey: "goosegrass", categoryId: 9, descKey: "goosegrassDesc", accuracy: "95.2%", harmLevel: "高" },
      { id: 46, nameKey: "purslane", categoryId: 9, descKey: "purslaneDesc", accuracy: "94.7%", harmLevel: "低" },
      { id: 47, nameKey: "alligatorWeed", categoryId: 9, descKey: "alligatorWeedDesc", accuracy: "93.8%", harmLevel: "高" },
    ],
  },
  {
    id: 10,
    nameKey: "categoryPhysiological",
    icon: Message,
    color: "#8b5cf6",
    cropKey: "cropGeneral",
    targets: [
      { id: 48, nameKey: "nitrogenDeficiency", categoryId: 10, descKey: "nitrogenDeficiencyDesc", accuracy: "98.5%", harmLevel: "中" },
      { id: 49, nameKey: "phosphorusDeficiency", categoryId: 10, descKey: "phosphorusDeficiencyDesc", accuracy: "97.2%", harmLevel: "中" },
      { id: 50, nameKey: "potassiumDeficiency", categoryId: 10, descKey: "potassiumDeficiencyDesc", accuracy: "96.6%", harmLevel: "中" },
      { id: 51, nameKey: "phytotoxicity", categoryId: 10, descKey: "phytotoxicityDesc", accuracy: "95.8%", harmLevel: "高" },
      { id: 52, nameKey: "droughtDamage", categoryId: 10, descKey: "droughtDamageDesc", accuracy: "94.9%", harmLevel: "高" },
      { id: 53, nameKey: "floodDamage", categoryId: 10, descKey: "floodDamageDesc", accuracy: "94.1%", harmLevel: "高" },
      { id: 54, nameKey: "frostDamage", categoryId: 10, descKey: "frostDamageDesc", accuracy: "93.5%", harmLevel: "高" },
    ],
  },
]);

const filteredCategories = computed(() => {
  if (!searchQuery.value) {
    return categories.value;
  }
  const query = searchQuery.value.toLowerCase();
  return categories.value.map((category) => ({
    ...category,
    targets: category.targets.filter((target) =>
      t(`targets.${target.nameKey}`).toLowerCase().includes(query)
    ),
  })).filter((category) =>
    t(`targets.${category.nameKey}`).toLowerCase().includes(query) || category.targets.length > 0
  );
});

const totalTargets = computed(() => {
  return categories.value.reduce((sum, category) => sum + category.targets.length, 0);
});

const getCategoryColor = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? category.color : "#6b7280";
};

const getCategoryIcon = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? category.icon : Message;
};

const getCategoryName = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? t(`targets.${category.nameKey}`) : t('targets.unknown');
};

const getCategoryCrop = (categoryId) => {
  const category = categories.value.find((c) => c.id === categoryId);
  return category ? t(`targets.${category.cropKey}`) : t('targets.unknown');
};

const getHarmLevelText = (level) => {
  const texts = {
    "高": t('targets.high'),
    "中": t('targets.medium'),
    "低": t('targets.low'),
  };
  return texts[level] || level;
};

const showTargetDetail = (target) => {
  selectedTarget.value = target;
  showDialog.value = true;
};
</script>

<style scoped lang="scss">
.targets-page {
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

  .search-container {
    margin-bottom: 24px;

    .search-input {
      max-width: 300px;
    }
  }

  .stats-cards {
    display: flex;
    gap: 20px;
    margin-bottom: 24px;

    .stat-card {
      flex: 1;
      max-width: 200px;
      background-color: #ffffff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      display: flex;
      align-items: center;
      gap: 16px;

      .stat-icon {
        width: 50px;
        height: 50px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;

        &.target-icon {
          background-color: #27ae60;
        }

        &.category-icon {
          background-color: #3b82f6;
        }
      }

      .stat-info {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .stat-label {
          font-size: 13px;
          color: var(--text-secondary);
        }
      }
    }
  }

  .target-categories {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;

    .category-card {
      background-color: #ffffff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      transition: all 0.2s;

      &:hover {
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
      }

      .category-header {
        display: flex;
        align-items: center;
        margin-bottom: 16px;

        .category-icon {
          width: 50px;
          height: 50px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 24px;
          margin-right: 16px;
        }

        .category-info {
          .category-name {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .category-count {
            font-size: 13px;
            color: var(--text-secondary);
          }
        }
      }

      .target-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .target-item {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          background-color: #f3f4f6;
          border-radius: 20px;
          font-size: 14px;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all 0.2s;

          &:hover {
            background-color: rgba(39, 174, 96, 0.1);
            color: #27ae60;
          }

          .target-item-icon {
            color: #27ae60;
          }
        }
      }
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
    }
  }

  .target-detail {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;

    .detail-icon {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-bottom: 20px;
    }

    .detail-info {
      width: 100%;

      .detail-item {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f3f4f6;

        &:last-child {
          border-bottom: none;
        }

        .detail-label {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .detail-value {
          font-size: 14px;
          color: var(--text-primary);
          font-weight: 500;
        }

        .harm-level {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 13px;
          
          &.高 {
            background-color: rgba(239, 68, 68, 0.1);
            color: #ef4444;
          }
          
          &.中 {
            background-color: rgba(245, 158, 11, 0.1);
            color: #f59e0b;
          }
          
          &.低 {
            background-color: rgba(34, 197, 96, 0.1);
            color: #22c55e;
          }
        }
      }
    }
  }
}
</style>
