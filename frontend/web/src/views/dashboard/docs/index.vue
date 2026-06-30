<template>
  <div class="document-center-page">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="document-center-header">
        <div>
          <h1>文档中心</h1>
          <p>集中管理转写稿、转换文档、知识库素材与导出记录。</p>
        </div>
        <ElButton type="primary">
          <FaSvgIcon icon="ri:add-line" />
          新建文档
        </ElButton>
      </section>

      <section class="quick-grid">
        <article v-for="item in quickActions" :key="item.title" class="quick-card fa-card">
          <div class="quick-icon">
            <FaSvgIcon :icon="item.icon" />
          </div>
          <h2>{{ item.title }}</h2>
          <p>{{ item.description }}</p>
        </article>
      </section>

      <section class="document-layout">
        <div class="fa-card document-list-card">
          <div class="section-header">
            <div>
              <h2>最近文档</h2>
              <p>按更新时间展示近期处理的文档内容。</p>
            </div>
            <ElButton text type="primary">
              查看全部
              <FaSvgIcon icon="ri:arrow-right-s-line" />
            </ElButton>
          </div>

          <ElTable :data="documents" class="document-table">
            <ElTableColumn prop="name" label="文档名称" min-width="180" />
            <ElTableColumn prop="type" label="类型" width="130" />
            <ElTableColumn label="状态" width="120">
              <template #default="{ row }">
                <ElTag :type="row.statusType">{{ row.status }}</ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="updatedAt" label="更新时间" width="160" />
            <ElTableColumn label="操作" width="140" fixed="right">
              <template #default>
                <ElButton link type="primary">打开</ElButton>
                <ElButton link>导出</ElButton>
              </template>
            </ElTableColumn>
          </ElTable>
        </div>

        <aside class="fa-card storage-card">
          <div class="section-header">
            <div>
              <h2>空间概览</h2>
              <p>文档资产与处理额度。</p>
            </div>
            <FaSvgIcon icon="ri:database-2-line" />
          </div>

          <div class="storage-meter">
            <ElProgress type="circle" :percentage="68" :width="132" />
            <div>
              <strong>68%</strong>
              <span>本月额度使用</span>
            </div>
          </div>

          <div class="storage-stats">
            <div v-for="item in stats" :key="item.label">
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </aside>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";

defineOptions({ name: "DashboardDocumentCenter" });

const loading = ref(true);

const quickActions = [
  {
    title: "音视频转写",
    description: "会议、访谈与课程素材快速生成文字稿。",
    icon: "ri:voiceprint-line",
  },
  {
    title: "AI文档转换",
    description: "多格式文档转换为可编辑内容与知识片段。",
    icon: "ri:file-transfer-line",
  },
  {
    title: "文档归档",
    description: "按项目、来源、标签统一整理文档资产。",
    icon: "ri:archive-drawer-line",
  },
];

const documents = [
  {
    name: "产品需求评审会议文字稿",
    type: "转写稿",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 10:20",
  },
  {
    name: "项目实施方案",
    type: "转换文档",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 09:50",
  },
  {
    name: "行业研究报告知识片段",
    type: "知识库",
    status: "处理中",
    statusType: "warning",
    updatedAt: "2026-06-29 18:12",
  },
];

const stats = [
  { label: "文档数", value: "128" },
  { label: "转写时长", value: "42h" },
  { label: "转换任务", value: "76" },
];

onMounted(() => {
  loading.value = false;
});
</script>

<style lang="scss" scoped>
.document-center-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 8px;
}

.document-center-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 8px 0 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.quick-card {
  padding: 20px;
  border-radius: 8px;

  h2 {
    margin: 14px 0 8px;
    font-size: 16px;
    font-weight: 650;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: var(--el-text-color-secondary);
  }
}

.quick-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  font-size: 24px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
}

.document-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
}

.document-list-card,
.storage-card {
  padding: 20px;
  border-radius: 8px;
}

.section-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;

  h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 650;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 6px 0 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  > .fa-svg-icon {
    flex: 0 0 auto;
    font-size: 24px;
    color: var(--el-color-primary);
  }
}

.document-table {
  width: 100%;
}

.storage-meter {
  display: flex;
  gap: 18px;
  align-items: center;

  strong,
  span {
    display: block;
  }

  strong {
    font-size: 28px;
    color: var(--el-text-color-primary);
  }

  span {
    margin-top: 6px;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

.storage-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 22px;

  div {
    padding: 12px;
    text-align: center;
    background: var(--el-fill-color-lighter);
    border-radius: 8px;
  }

  strong,
  span {
    display: block;
  }

  strong {
    font-size: 18px;
    color: var(--el-text-color-primary);
  }

  span {
    margin-top: 4px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

@media screen and (width <= 1100px) {
  .document-layout,
  .quick-grid {
    grid-template-columns: 1fr;
  }
}

@media screen and (width <= 640px) {
  .document-center-header {
    flex-direction: column;
  }
}
</style>
