<template>
  <div class="document-center-page">
    <FaDashboardSkeleton v-if="loading" />
    <template v-else>
      <section class="document-center-header">
        <div>
          <h1>文档中心</h1>
          <p>
            当前知识库仅支持 .txt / .md / .markdown / .csv / .pdf / .docx / .xlsx。旧版 Office
            和演示文稿格式已禁用，避免乱码和误解析。
          </p>
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
            <div class="section-header__content">
              <h2>最近文档</h2>
              <p>按更新时间展示近期处理的文档内容。</p>
            </div>
            <ElInput
              v-model.trim="searchKeyword"
              class="document-search"
              clearable
              :prefix-icon="Search"
              placeholder="搜索文档名称"
            />
          </div>

          <ElTable :data="paginatedDocuments" class="document-table">
            <ElTableColumn prop="name" label="文档名称" min-width="180" />
            <ElTableColumn prop="user" label="创建人" width="130" />
            <ElTableColumn prop="type" label="类型" width="130" />
            <ElTableColumn label="状态" width="120">
              <template #default="{ row }">
                <ElTag :type="row.statusType">{{ row.status }}</ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="updatedAt" label="更新时间" width="160" />
            <ElTableColumn label="操作" width="240" fixed="right">
              <template #default>
                <div class="table-actions">
                  <ElButton link type="primary">打开</ElButton>
                  <ElButton link>共享</ElButton>
                  <ElButton link>导出</ElButton>
                  <ElButton link>删除</ElButton>
                </div>
              </template>
            </ElTableColumn>
          </ElTable>

          <div class="table-pagination">
            <div class="table-pagination__summary">
              共 {{ filteredDocuments.length }} 条数据，当前第 {{ displayCurrentPage }} /
              {{ totalPages }} 页
            </div>
            <ElPagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              :total="filteredDocuments.length"
              background
              layout="sizes, prev, pager, next"
            />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Search } from "@element-plus/icons-vue";
import FaDashboardSkeleton from "@/components/skeleton/fa-dashboard-skeleton.vue";

defineOptions({ name: "DashboardDocumentCenter" });

const loading = ref(true);
const searchKeyword = ref("");
const currentPage = ref(1);
const pageSize = ref(10);

const quickActions = [
  {
    title: "可见文档",
    description: "按项目、来源、标签统一整理文档资产。",
    icon: "ri:voiceprint-line",
  },
  {
    title: "可管理文档",
    description: "多格式文档转换为可编辑内容与知识片段。",
    icon: "ri:file-transfer-line",
  },
  {
    title: "共享文档",
    description: "按项目、来源、标签统一整理文档资产。",
    icon: "ri:archive-drawer-line",
  },
  {
    title: "已完成",
    description: "按项目、来源、标签统一整理文档资产。",
    icon: "ri:archive-drawer-line",
  },
];

const documents = [
  {
    name: "产品需求评审会议文字稿",
    user: "user",
    type: "转写稿",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 10:20",
  },
  {
    name: "项目实施方案",
    user: "user",
    type: "转换文档",
    status: "已完成",
    statusType: "success",
    updatedAt: "2026-06-30 09:50",
  },
  {
    name: "行业研究报告知识片段",
    user: "user",
    type: "知识库",
    status: "处理中",
    statusType: "warning",
    updatedAt: "2026-06-29 18:12",
  },
];

const filteredDocuments = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return documents;
  return documents.filter((item) => item.name.toLowerCase().includes(keyword));
});

const paginatedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredDocuments.value.slice(start, start + pageSize.value);
});

const totalPages = computed(() => {
  if (filteredDocuments.value.length === 0) return 0;
  return Math.ceil(filteredDocuments.value.length / pageSize.value);
});

const displayCurrentPage = computed(() => {
  if (filteredDocuments.value.length === 0) return 0;
  return Math.min(currentPage.value, totalPages.value);
});

watch([searchKeyword, pageSize], () => {
  currentPage.value = 1;
});

watch([filteredDocuments, totalPages], () => {
  if (totalPages.value === 0) {
    currentPage.value = 1;
    return;
  }
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
});

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
  align-items: center;
  justify-content: space-between;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 6px 0 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.quick-card {
  padding: 16px 18px;
  border-radius: 8px;

  h2 {
    margin: 12px 0 6px;
    font-size: 15px;
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
  width: 40px;
  height: 40px;
  font-size: 22px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  border-radius: 8px;
}

.document-layout {
  display: flex;
}

.document-list-card,
.storage-card {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 18px;
  border-radius: 8px;
}

.section-header {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;

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

.section-header__content {
  min-width: 0;
}

.document-search {
  flex: 0 0 240px;
  max-width: 100%;
}

.document-table {
  width: 100%;
}

.table-pagination {
  display: flex;
  flex-shrink: 0;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.table-pagination__summary {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.table-pagination :deep(.el-pagination) {
  margin-left: auto;
}

.table-pagination :deep(.el-pagination__sizes) {
  margin-right: 8px;
}

@media screen and (width <= 640px) {
  .table-pagination {
    align-items: flex-start;
  }

  .table-pagination :deep(.el-pagination) {
    margin-left: 0;
  }
}

.table-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
  white-space: nowrap;
}

.table-actions :deep(.el-button) {
  margin: 0;
  min-height: auto;
  padding: 0;
}

@media screen and (width <= 1100px) {
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media screen and (width <= 640px) {
  .document-center-header,
  .section-header {
    flex-direction: column;
  }

  .document-search {
    flex-basis: auto;
    width: 100%;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
